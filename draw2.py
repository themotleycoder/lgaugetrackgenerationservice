import drawsvg as draw
import math
from dataclasses import dataclass
from typing import List, Tuple, Literal

@dataclass
class TrackPiece:
    type: Literal['straight', 'curve', 'switch']
    direction: Literal['left', 'right'] = 'right'
    angle: float = 0

class TrackSystem:
    def __init__(self, width=4096, height=4096):
        # Using a much larger viewBox for bigger layouts
        self.drawing = draw.Drawing(width, height, origin='center', viewBox='-2048 -2048 4096 4096')
        self.track_width = 80  
        self.straight_length = 160
        self.curve_radius = 400
        self.curve_left_vertical_offset = 27.5
        
        # Add zoom controls
        self.add_zoom_controls()
        
        # Load SVG files
        self.pieces = {}
        self.load_svg_files()

    def add_zoom_controls(self):
        """Add zoom in/out buttons to the SVG"""
        # Add a script to handle zooming
        script = """
            <script type="text/javascript">
                <![CDATA[
                    var currentScale = 1.0;
                    var mainGroup = document.getElementById('main-group');
                    
                    function zoomIn() {
                        currentScale = Math.min(currentScale * 1.2, 3.0);
                        updateZoom();
                    }
                    
                    function zoomOut() {
                        currentScale = Math.max(currentScale / 1.2, 0.2);
                        updateZoom();
                    }
                    
                    function updateZoom() {
                        mainGroup.setAttribute('transform', 'scale(' + currentScale + ')');
                    }
                ]]>
            </script>
        """
        self.drawing.append(draw.Raw(script))

        # Add zoom buttons
        buttons_style = """
            <style>
                .zoom-btn {
                    fill: #f0f0f0;
                    stroke: #666;
                    stroke-width: 1;
                    cursor: pointer;
                }
                .zoom-btn:hover {
                    fill: #e0e0e0;
                }
                .zoom-text {
                    font-family: Arial;
                    user-select: none;
                    pointer-events: none;
                }
            </style>
        """
        self.drawing.append(draw.Raw(buttons_style))

        # Zoom in button
        zoom_in_group = draw.Group()
        zoom_in_btn = draw.Circle(-1900, -1900, 40, fill='#f0f0f0', stroke='#666', 
                                stroke_width=2, class_='zoom-btn', 
                                onclick='zoomIn()')
        zoom_in_text = draw.Text('+', x=-1915, y=-1885, font_size=48, class_='zoom-text')
        zoom_in_group.append(zoom_in_btn)
        zoom_in_group.append(zoom_in_text)
        self.drawing.append(zoom_in_group)

        # Zoom out button
        zoom_out_group = draw.Group()
        zoom_out_btn = draw.Circle(-1900, -1780, 40, fill='#f0f0f0', stroke='#666', 
                                 stroke_width=2, class_='zoom-btn', 
                                 onclick='zoomOut()')
        zoom_out_text = draw.Text('-', x=-1915, y=-1765, font_size=48, class_='zoom-text')
        zoom_out_group.append(zoom_out_btn)
        zoom_out_group.append(zoom_out_text)
        self.drawing.append(zoom_out_group)

        # Create a main group for the track pieces that will be scaled
        self.main_group = draw.Group(id='main-group')
        self.drawing.append(self.main_group)

    def load_svg_files(self):
        """Load SVG files for each track piece"""
        svg_files = {
            'straight': 'svgs/straight.svg',
            'curve_left': 'svgs/curve_left.svg',
            'curve_right': 'svgs/curve_right.svg',
            'switch_left': 'svgs/switch_left.svg',
            'switch_right': 'svgs/switch_right.svg'
        }
        
        for piece_type, filename in svg_files.items():
            try:
                with open(filename, 'r') as f:
                    svg_content = f.read()
                    start_idx = svg_content.find('>')
                    end_idx = svg_content.rfind('</')
                    if start_idx != -1 and end_idx != -1:
                        self.pieces[piece_type] = svg_content[start_idx + 1:end_idx]
            except FileNotFoundError:
                print(f"Warning: Could not load {filename}")

    def add_track_piece(self, x: float, y: float, angle: float, piece_type: str, direction: str = 'right') -> None:
        """Add a track piece SVG at the specified position and rotation"""
        if piece_type == 'curve':
            svg_key = f'curve_{direction}'
        elif piece_type == 'switch':
            svg_key = f'switch_{direction}'
        else:
            svg_key = 'straight'
            
        if svg_key not in self.pieces:
            print(f"Warning: Missing SVG for {svg_key}")
            return
            
        svg_content = self.pieces[svg_key]
        g = draw.Group()
        g.append(draw.Raw(svg_content))
        transform = f"translate({x},{y}) rotate({angle})"
        g.args["transform"] = transform
        
        # Add to main group instead of directly to drawing
        self.main_group.append(g)

    def add_straight_segment(self, x: float, y: float, angle: float) -> Tuple[float, float, float]:
        """Add a straight track piece and return ending position and angle"""
        self.add_track_piece(x, y, angle, 'straight')
        
        # Calculate end position
        rad = math.radians(angle)
        end_x = x + self.straight_length * math.cos(rad)
        end_y = y + self.straight_length * math.sin(rad)
        
        return (end_x, end_y, angle)

    def add_curved_segment(self, x: float, y: float, angle: float, direction: str = 'right') -> Tuple[float, float, float]:
        """Add a curved track piece and return ending position and angle"""
        # Calculate end position
        sweep_angle = 22.5  # Degrees
        end_angle = angle + (sweep_angle if direction == 'right' else -sweep_angle)
        rad = math.radians(angle)
        
        if direction == 'right':
            # Right curve parameters (these work well)
            self.add_track_piece(x, y, angle, 'curve', direction)
            dx = 170.5
            dy = 33.5
        else:
            # For left curves, we need to flip the vertical offset based on the current angle
            # Calculate if we're in the "flipped" state (between 90 and 270 degrees)
            normalized_angle = angle % 360
            if normalized_angle < 0:
                normalized_angle += 360
            is_flipped = 90 < normalized_angle < 270
            
            # Apply the vertical offset with the correct sign based on orientation
            vertical_offset = self.curve_left_vertical_offset * (-1 if is_flipped else 1)
            self.add_track_piece(x, y - vertical_offset, angle, 'curve', direction)
            
            dx = 140
            dy = -27.5  # Base offset
            # Flip dy if we're in the inverted state
            # if is_flipped:
            #     dy *= -1
                
        
        # Apply rotation matrix to the offset
        cos_angle = math.cos(rad)
        sin_angle = math.sin(rad)
        end_x = x + (dx * cos_angle - dy * sin_angle)
        end_y = y + (dx * sin_angle + dy * cos_angle)
                
        return (end_x, end_y, end_angle)

    def add_switch_segment(self, x: float, y: float, angle: float, direction: str = 'right') -> Tuple[float, float, float, float, float, float]:
        """Add a switch track piece and return ending positions and angles for both routes"""
        self.add_track_piece(x, y, angle, 'switch', direction)
        
        # Calculate endpoints    
        switch_length = self.straight_length * 2  # 32 studs
        diverge_angle = 22.5  # Standard LEGO curve angle
        
        # Straight route end
        rad = math.radians(angle)
        straight_end_x = x + switch_length * math.cos(rad)
        straight_end_y = y + switch_length * math.sin(rad)
        
        # Diverging route end
        diverging_end_angle = angle + (diverge_angle if direction == 'right' else -diverge_angle)
        div_rad = math.radians(angle)
        
        # Fine-tuned offsets based on SVG analysis
        if direction == 'right':
            dx = 339.5  # Measured from SVG
            dy = 132.5   # Measured from SVG
            diverging_end_x = x + (dx * math.cos(div_rad) - dy * math.sin(div_rad))
            diverging_end_y = y + (dx * math.sin(div_rad) + dy * math.cos(div_rad))
        else:
            dx = 282.84
            dy = -115.8
            diverging_end_x = x + (dx * math.cos(div_rad) - dy * math.sin(div_rad))
            diverging_end_y = y + (dx * math.sin(div_rad) + dy * math.cos(div_rad))
        
        return (straight_end_x, straight_end_y, angle,
                diverging_end_x, diverging_end_y, diverging_end_angle)

    def create_track_layout(self, pieces: List[TrackPiece]):
        """Create a track layout from a sequence of track pieces"""
        paths = [(0, 0, 0)]  # List of (x, y, angle) tuples
        
        for piece in pieces:
            new_paths = []
            for current_x, current_y, current_angle in paths:
                if piece.type == 'curve':
                    end_x, end_y, end_angle = self.add_curved_segment(
                        current_x, current_y, current_angle, piece.direction
                    )
                    new_paths.append((end_x, end_y, end_angle))
                elif piece.type == 'switch':
                    straight_end_x, straight_end_y, straight_angle, \
                    diverging_end_x, diverging_end_y, diverging_angle = self.add_switch_segment(
                        current_x, current_y, current_angle, piece.direction
                    )
                    new_paths.extend([
                        (straight_end_x, straight_end_y, straight_angle),
                        (diverging_end_x, diverging_end_y, diverging_angle)
                    ])
                else:  # straight
                    end_x, end_y, end_angle = self.add_straight_segment(
                        current_x, current_y, current_angle
                    )
                    new_paths.append((end_x, end_y, end_angle))
            paths = new_paths

def create_example_layout():
    track = TrackSystem()
    
    # Layout matching the reference image
    layout = [
        # Start with straight piece
        TrackPiece(type='straight'),
        
        # First left turn
        TrackPiece(type='curve', direction='left'),
        
        # Straight section after left turn
        TrackPiece(type='straight'),
        
        # Large right curve section (approximately 10-11 curve pieces to form most of a circle)
        TrackPiece(type='curve', direction='right'),
        TrackPiece(type='curve', direction='right'),
        TrackPiece(type='curve', direction='right'),
        TrackPiece(type='curve', direction='right'),
        TrackPiece(type='curve', direction='right'),
        TrackPiece(type='curve', direction='right'),
        TrackPiece(type='curve', direction='right'),
        TrackPiece(type='curve', direction='right'),
        TrackPiece(type='curve', direction='right'),
        TrackPiece(type='curve', direction='right'),
        
        # Straight section before final left turn
        TrackPiece(type='straight'),
        
        # Final left turn
        TrackPiece(type='curve', direction='left'),
        
        # Final straight piece
        TrackPiece(type='straight'),
    ]
    
    track.create_track_layout(layout)
    track.drawing.save_svg('lego_track_layout.svg')

if __name__ == "__main__":
    create_example_layout()