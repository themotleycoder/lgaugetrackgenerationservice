import drawsvg as draw
import math
from dataclasses import dataclass
from typing import List, Tuple, Literal
import os

@dataclass
class TrackPiece:
    type: Literal['straight', 'curve', 'switch']
    color: str
    direction: Literal['left', 'right'] = 'right'  # Default to right curve/switch
    angle: float = 0
    
class TrackSystem:
    def __init__(self, width=800, height=800):
        self.drawing = draw.Drawing(width, height, origin='center', viewBox='-300 -300 600 600')
        self.track_width = 8  # 8 studs wide
        self.straight_length = 16  # 16 studs long
        self.curve_outer_radius = 40  # 40 studs
        self.curve_inner_radius = 32  # 32 studs
        
    def create_curved_segment(self, x: float, y: float, angle: float, color: str, direction: str = 'right') -> Tuple[float, float, float]:
        """Creates a curved track segment and returns ending position and angle"""
        start_rad = math.radians(angle)
        sweep_angle = 22.5  # Degrees
        # For left curves, subtract the sweep angle instead of adding
        end_angle = angle + sweep_angle if direction == 'right' else angle - sweep_angle
        end_rad = math.radians(end_angle)
        
        # Calculate center point of the curve - mirror for left curves
        if direction == 'right':
            center_x = x - self.curve_outer_radius * math.sin(start_rad)
            center_y = y + self.curve_outer_radius * math.cos(start_rad)
            outer_end_x = center_x + self.curve_outer_radius * math.sin(end_rad)
            outer_end_y = center_y - self.curve_outer_radius * math.cos(end_rad)
        else:  # left curve
            center_x = x + self.curve_outer_radius * math.sin(start_rad)
            center_y = y - self.curve_outer_radius * math.cos(start_rad)
            outer_end_x = center_x - self.curve_outer_radius * math.sin(end_rad)
            outer_end_y = center_y + self.curve_outer_radius * math.cos(end_rad)
        
        # Start point is the same for both directions
        outer_start_x = x
        outer_start_y = y
        
        # Calculate inner points parallel to the curve at start and end
        inner_start_x = x - self.track_width * math.cos(start_rad - math.pi/2)
        inner_start_y = y - self.track_width * math.sin(start_rad - math.pi/2)
        inner_end_x = outer_end_x - self.track_width * math.cos(end_rad - math.pi/2)
        inner_end_y = outer_end_y - self.track_width * math.sin(end_rad - math.pi/2)
        
        p = draw.Path(fill=color, stroke='black', stroke_width=0.5)
        
        # Draw the curved piece
        p.M(outer_start_x, outer_start_y)  # Start at outer edge
        # Reverse sweep flags for left curves
        sweep_flag_outer = 1 if direction == 'right' else 0
        sweep_flag_inner = 0 if direction == 'right' else 1
        p.A(self.curve_outer_radius, self.curve_outer_radius, 0, 0, sweep_flag_outer,
            outer_end_x, outer_end_y)  # Draw outer curve
        p.L(inner_end_x, inner_end_y)  # Draw end cap
        p.A(self.curve_inner_radius, self.curve_inner_radius, 0, 0, sweep_flag_inner,
            inner_start_x, inner_start_y)  # Draw inner curve
        p.L(outer_start_x, outer_start_y)  # Connect back to start
        
        p.Z()
        self.drawing.append(p)
        
        return (outer_end_x, outer_end_y, end_angle)
        
    def create_straight_segment(self, x: float, y: float, angle: float, color: str) -> Tuple[float, float, float]:
        """Creates a straight track segment and returns ending position and angle"""
        rad = math.radians(angle)
        
        # Calculate the four corners of the straight piece
        # Start points
        start_outer_x = x
        start_outer_y = y
        start_inner_x = x - self.track_width * math.cos(rad - math.pi/2)
        start_inner_y = y - self.track_width * math.sin(rad - math.pi/2)
        
        # End points
        end_outer_x = x + self.straight_length * math.cos(rad)
        end_outer_y = y + self.straight_length * math.sin(rad)
        end_inner_x = end_outer_x - self.track_width * math.cos(rad - math.pi/2)
        end_inner_y = end_outer_y - self.track_width * math.sin(rad - math.pi/2)
        
        p = draw.Path(fill=color, stroke='black', stroke_width=0.5)
        
        # Draw the straight piece
        p.M(start_outer_x, start_outer_y)  # Start at outer edge
        p.L(end_outer_x, end_outer_y)  # Draw outer edge
        p.L(end_inner_x, end_inner_y)  # Draw end cap
        p.L(start_inner_x, start_inner_y)  # Draw inner edge
        p.Z()  # Close path back to start
        
        self.drawing.append(p)
        
        return (end_outer_x, end_outer_y, angle)
        
    def create_switch_segment(self, x: float, y: float, angle: float, color: str, direction: str = 'right') -> Tuple[float, float, float, float, float, float]:
        """Creates a switch track segment and returns ending positions and angles for both routes"""
        rad = math.radians(angle)
        switch_length = 32  # 32 studs long
        crossing_angle = math.radians(32.5)  # 32.5° crossing vee
        diverging_angle = 22.5  # 22.5° diverging route (in degrees for return value)
        diverging_rad = math.radians(diverging_angle)  # Convert to radians for calculations
        
        # Calculate straight route endpoints
        straight_end_x = x + switch_length * math.cos(rad)
        straight_end_y = y + switch_length * math.sin(rad)
        
        # Calculate diverging route endpoints
        diverging_rad = rad + (diverging_rad if direction == 'right' else -diverging_rad)
        diverging_end_x = x + switch_length * math.cos(diverging_rad)
        diverging_end_y = y + switch_length * math.sin(diverging_rad)
        
        # Calculate control points for the diverging curve
        # The control point is where the straight and diverging routes split
        split_distance = switch_length * 0.3  # Split point at 30% of the length
        split_x = x + split_distance * math.cos(rad)
        split_y = y + split_distance * math.sin(rad)
        
        # Draw main route (straight path)
        p_straight = draw.Path(fill=color, stroke='black', stroke_width=0.5)
        
        # Start point coordinates
        start_outer_x = x
        start_outer_y = y
        start_inner_x = x - self.track_width * math.cos(rad - math.pi/2)
        start_inner_y = y - self.track_width * math.sin(rad - math.pi/2)
        
        # Straight route end coordinates
        straight_end_inner_x = straight_end_x - self.track_width * math.cos(rad - math.pi/2)
        straight_end_inner_y = straight_end_y - self.track_width * math.sin(rad - math.pi/2)
        
        # Draw straight route
        p_straight.M(start_outer_x, start_outer_y)
        p_straight.L(straight_end_x, straight_end_y)
        p_straight.L(straight_end_inner_x, straight_end_inner_y)
        p_straight.L(start_inner_x, start_inner_y)
        p_straight.Z()
        self.drawing.append(p_straight)
        
        # Draw diverging route
        p_diverging = draw.Path(fill=color, stroke='black', stroke_width=0.5)
        
        # Diverging route end coordinates
        diverging_end_inner_x = diverging_end_x - self.track_width * math.cos(diverging_rad - math.pi/2)
        diverging_end_inner_y = diverging_end_y - self.track_width * math.sin(diverging_rad - math.pi/2)
        
        # Draw diverging route from split point
        p_diverging.M(split_x, split_y)
        p_diverging.L(diverging_end_x, diverging_end_y)
        p_diverging.L(diverging_end_inner_x, diverging_end_inner_y)
        p_diverging.L(split_x - self.track_width * math.cos(rad - math.pi/2),
                     split_y - self.track_width * math.sin(rad - math.pi/2))
        p_diverging.Z()
        self.drawing.append(p_diverging)
        
        # Return both endpoints with their respective angles
        diverging_end_angle = angle + (diverging_angle if direction == 'right' else -diverging_angle)
        print(f"Switch angles - Straight: {angle}, Diverging: {diverging_end_angle}")  # Debug print
        return (straight_end_x, straight_end_y, angle,
                diverging_end_x, diverging_end_y, diverging_end_angle)

    def draw_track_sequence(self, pieces: List[TrackPiece]):
        """Draw a sequence of track pieces that connect properly"""
        # Track state maintains multiple possible paths after switches
        paths = [(0, 0, 0)]  # List of (x, y, angle) tuples
        
        for piece in pieces:
            new_paths = []
            for current_x, current_y, current_angle in paths:
                if piece.type == 'curve':
                    end_x, end_y, end_angle = self.create_curved_segment(
                        current_x, current_y, current_angle, piece.color, piece.direction
                    )
                    new_paths.append((end_x, end_y, end_angle))
                elif piece.type == 'switch':
                    # Switch creates two paths - straight and diverging
                    straight_end_x, straight_end_y, straight_angle, \
                    diverging_end_x, diverging_end_y, diverging_angle = self.create_switch_segment(
                        current_x, current_y, current_angle, piece.color, piece.direction
                    )
                    new_paths.extend([
                        (straight_end_x, straight_end_y, straight_angle),
                        (diverging_end_x, diverging_end_y, diverging_angle)
                    ])
                else:  # straight
                    end_x, end_y, end_angle = self.create_straight_segment(
                        current_x, current_y, current_angle, piece.color
                    )
                    new_paths.append((end_x, end_y, end_angle))
            paths = new_paths

# Example usage
track = TrackSystem()

# Define track sequence with branching paths
main_path = [
    TrackPiece(type='straight', color='blue'),
    TrackPiece(type='switch', color='red', direction='right')
]

# After switch, define separate pieces for each path
straight_path = [
    TrackPiece(type='straight', color='green'),
    TrackPiece(type='straight', color='green')
]

diverging_path = [
    TrackPiece(type='curve', color='purple', direction='left'),  # Match switch direction
    TrackPiece(type='straight', color='green')
]

# Draw main path up to switch
track.draw_track_sequence(main_path)

# Get the last piece (switch) endpoints
paths = [(0, 0, 0)]  # Initial position
for piece in main_path:
    new_paths = []
    for x, y, angle in paths:
        if piece.type == 'switch':
            straight_end_x, straight_end_y, straight_angle, \
            diverging_end_x, diverging_end_y, diverging_angle = track.create_switch_segment(
                x, y, angle, piece.color, piece.direction
            )
            # Store both endpoints
            new_paths.extend([
                (straight_end_x, straight_end_y, straight_angle),
                (diverging_end_x, diverging_end_y, diverging_angle)
            ])
        elif piece.type == 'curve':
            end_x, end_y, end_angle = track.create_curved_segment(
                x, y, angle, piece.color, piece.direction
            )
            new_paths.append((end_x, end_y, end_angle))
        else:  # straight
            end_x, end_y, end_angle = track.create_straight_segment(
                x, y, angle, piece.color
            )
            new_paths.append((end_x, end_y, end_angle))
    paths = new_paths

# Draw straight path from first endpoint
x, y, angle = paths[0]
current_x, current_y, current_angle = x, y, angle
for piece in straight_path:
    if piece.type == 'curve':
        current_x, current_y, current_angle = track.create_curved_segment(
            current_x, current_y, current_angle, piece.color, piece.direction
        )
    else:  # straight
        current_x, current_y, current_angle = track.create_straight_segment(
            current_x, current_y, current_angle, piece.color
        )

# Draw diverging path from second endpoint
x, y, angle = paths[1]  # This contains the diverging endpoint and angle
current_x, current_y, current_angle = x, y, angle
print(f"Diverging path starting angle: {current_angle}")  # Debug print

for piece in diverging_path:
    if piece.type == 'curve':
        # The angle from the switch already includes the diverging angle,
        # so we can directly use it for the curve
        current_x, current_y, current_angle = track.create_curved_segment(
            current_x, current_y, current_angle, piece.color, piece.direction
        )
        print(f"After curve: {current_angle}")  # Debug print
    else:  # straight
        current_x, current_y, current_angle = track.create_straight_segment(
            current_x, current_y, current_angle, piece.color
        )

track.draw_track_sequence([])  # Empty sequence to trigger drawing
track.drawing.set_pixel_scale(2)

# Save and display the drawing
track.drawing.save_svg('track_output.svg')
