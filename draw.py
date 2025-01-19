import drawsvg as draw
import math
from dataclasses import dataclass
from typing import List, Tuple, Literal
import os

@dataclass
class TrackPiece:
    type: Literal['straight', 'curve']
    color: str
    angle: float = 0
    
class TrackSystem:
    def __init__(self, width=800, height=600):
        self.drawing = draw.Drawing(width, height, origin='center', viewBox='-100 -150 300 300')
        self.track_width = 8  # 8 studs wide
        self.straight_length = 16  # 16 studs long
        self.curve_outer_radius = 40  # 40 studs
        self.curve_inner_radius = 32  # 32 studs
        
    def create_curved_segment(self, x: float, y: float, angle: float, color: str) -> Tuple[float, float, float]:
        """Creates a curved track segment and returns ending position and angle"""
        start_rad = math.radians(angle)
        sweep_angle = 22.5  # Degrees
        end_angle = angle + sweep_angle
        end_rad = math.radians(end_angle)
        
        # Calculate center point of the curve
        center_x = x - self.curve_outer_radius * math.sin(start_rad)
        center_y = y + self.curve_outer_radius * math.cos(start_rad)
        
        # Calculate start and end points for outer and inner curves
        outer_start_x = x
        outer_start_y = y
        outer_end_x = center_x + self.curve_outer_radius * math.sin(end_rad)
        outer_end_y = center_y - self.curve_outer_radius * math.cos(end_rad)
        
        # Calculate inner points parallel to the curve at start and end
        inner_start_x = x - self.track_width * math.cos(start_rad - math.pi/2)
        inner_start_y = y - self.track_width * math.sin(start_rad - math.pi/2)
        inner_end_x = outer_end_x - self.track_width * math.cos(end_rad - math.pi/2)
        inner_end_y = outer_end_y - self.track_width * math.sin(end_rad - math.pi/2)
        
        p = draw.Path(fill=color, stroke='black', stroke_width=0.5)
        
        # Draw the curved piece
        p.M(outer_start_x, outer_start_y)  # Start at outer edge
        p.A(self.curve_outer_radius, self.curve_outer_radius, 0, 0, 1,
            outer_end_x, outer_end_y)  # Draw outer curve
        p.L(inner_end_x, inner_end_y)  # Draw end cap
        p.A(self.curve_inner_radius, self.curve_inner_radius, 0, 0, 0,
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
                    current_x, current_y, current_angle, piece.color
                )
            else:  # straight
                current_x, current_y, current_angle = self.create_straight_segment(
                    current_x, current_y, current_angle, piece.color
                )

# Example usage
track = TrackSystem()

pieces = [
    TrackPiece(type='curve', color='red'),
    TrackPiece(type='curve', color='blue'),
    TrackPiece(type='curve', color='green'),
    TrackPiece(type='curve', color='yellow'),
    TrackPiece(type='straight', color='purple'),
    TrackPiece(type='straight', color='orange'),
    TrackPiece(type='curve', color='red'),
    TrackPiece(type='curve', color='blue'),
    TrackPiece(type='straight', color='purple'),
    TrackPiece(type='straight', color='orange'),
    TrackPiece(type='curve', color='green'),
    TrackPiece(type='curve', color='yellow'),
]

track.draw_track_sequence(pieces)
track.drawing.set_pixel_scale(2)

# Save and display the drawing
track.drawing.save_svg('track_output.svg')

# Open the SVG file in the default web browser
import webbrowser
webbrowser.open('file://' + os.path.realpath('track_output.svg'))
