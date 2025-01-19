import drawsvg as draw
import math
from dataclasses import dataclass
from typing import List, Tuple, Literal
import os

@dataclass
class TrackPiece:
    type: Literal['straight', 'curve']
    color: str
    direction: Literal['left', 'right'] = 'right'  # Default to right curve
    angle: float = 0
    
class TrackSystem:
    def __init__(self, width=800, height=600):
        self.drawing = draw.Drawing(width, height, origin='center', viewBox='-100 -150 300 300')
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

    def draw_track_sequence(self, pieces: List[TrackPiece]):
        """Draw a sequence of track pieces that connect properly"""
        current_x = 0
        current_y = 0
        current_angle = 0
        
        for piece in pieces:
            if piece.type == 'curve':
                current_x, current_y, current_angle = self.create_curved_segment(
                    current_x, current_y, current_angle, piece.color, piece.direction
                )
            else:  # straight
                current_x, current_y, current_angle = self.create_straight_segment(
                    current_x, current_y, current_angle, piece.color
                )

# Example usage
track = TrackSystem()

pieces = [
    # Start with right turn
    TrackPiece(type='curve', color='red', direction='right'),
    TrackPiece(type='curve', color='blue', direction='right'),
    TrackPiece(type='straight', color='purple'),
    # Left turn
    TrackPiece(type='curve', color='green', direction='left'),
    TrackPiece(type='curve', color='yellow', direction='left'),
    TrackPiece(type='straight', color='orange'),
    # Right turn
    TrackPiece(type='curve', color='red', direction='right'),
    TrackPiece(type='curve', color='blue', direction='right'),
    TrackPiece(type='straight', color='purple'),
    # Final left turn to complete the pattern
    TrackPiece(type='curve', color='green', direction='left'),
    TrackPiece(type='curve', color='yellow', direction='left'),
]

track.draw_track_sequence(pieces)
track.drawing.set_pixel_scale(2)

# Save and display the drawing
track.drawing.save_svg('track_output.svg')
