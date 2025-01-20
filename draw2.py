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
        self.track_width = 77  
        self.straight_length = 149
        self.curve_radius = 400
        
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
        
        # Constants for curve geometry
        dx = 159  # X offset for right curve
        dy = 31.2  # Y offset for right curve
        
        # Calculate offsets based on current angle
        if direction == 'right':
            self.add_track_piece(x, y, angle, 'curve', direction)
            # Apply rotation matrix to the offset
            cos_angle = math.cos(rad)
            sin_angle = math.sin(rad)
            end_x = x + (dx * cos_angle - dy * sin_angle)
            end_y = y + (dx * sin_angle + dy * cos_angle)
        else:
            self.add_track_piece(x, y-25.5, angle, 'curve', direction)
            # Different offsets for left curve
            dx = 120
            dy = -23
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
        rad = math.radians(angle)
        switch_length = self.straight_length * 2  # 32 studs long
        diverging_angle = 22.5  # 22.5° diverging route
        
        # Straight route end
        straight_end_x = x + switch_length * math.cos(rad)
        straight_end_y = y + switch_length * math.sin(rad)
        
        # Diverging route end
        diverging_end_angle = angle + (diverging_angle if direction == 'right' else -diverging_angle)
        diverging_rad = math.radians(diverging_end_angle)
        diverging_end_x = x + switch_length * math.cos(diverging_rad)
        diverging_end_y = y + switch_length * math.sin(diverging_rad)
        
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
    
    # Create a circle with 16 right curves
    # layout = [TrackPiece(type='curve', direction='left') for _ in range(16)]

    layout = [
        TrackPiece(type='straight'),
        TrackPiece(type='curve', direction='right'),
        TrackPiece(type='curve', direction='right'),
        TrackPiece(type='straight'),
        TrackPiece(type='curve', direction='right'),
        TrackPiece(type='curve', direction='right'),
        TrackPiece(type='curve', direction='right'),
        TrackPiece(type='curve', direction='right'),
        TrackPiece(type='curve', direction='right'),
        TrackPiece(type='curve', direction='right'),
        TrackPiece(type='straight'),
        TrackPiece(type='straight'),
        TrackPiece(type='curve', direction='right'),
        TrackPiece(type='curve', direction='right'),
        TrackPiece(type='straight'),
        TrackPiece(type='curve', direction='right'),
        TrackPiece(type='curve', direction='right'),
        TrackPiece(type='curve', direction='right'),
        TrackPiece(type='curve', direction='right'),
        TrackPiece(type='curve', direction='right'),
        TrackPiece(type='curve', direction='right'),
        TrackPiece(type='straight'),
    ]
    
    track.create_track_layout(layout)
    track.drawing.save_svg('lego_track_layout.svg')

if __name__ == "__main__":
    create_example_layout()