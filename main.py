from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Tuple, Optional
import math
import json
import uvicorn

@dataclass
class Point:
    x: float
    y: float
    
    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y)
        
    def __sub__(self, other):
        return Point(self.x - other.x, self.y - other.y)
        
    def distance_to(self, other) -> float:
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
    
    def rotate(self, angle_degrees: float) -> 'Point':
        """Rotate point around origin by given angle in degrees."""
        angle_rad = math.radians(angle_degrees)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        return Point(
            self.x * cos_a - self.y * sin_a,
            self.x * sin_a + self.y * cos_a
        )

@dataclass
class TrackGeometry:
    """Represents the geometry of a track piece."""
    start: Point
    end: Point
    angle: float  # degrees
    
    @staticmethod
    def from_straight(length: float = 16) -> 'TrackGeometry':
        """Create a straight track piece of given length."""
        return TrackGeometry(
            start=Point(0, 0),
            end=Point(length, 0),
            angle=0
        )
    
    @staticmethod
    def from_curve() -> 'TrackGeometry':
        """Create a standard LEGO curved track piece.
        - 40 stud radius
        - 22.5 degrees of arc
        """
        RADIUS = 40
        ANGLE = 22.5
        angle_rad = math.radians(ANGLE)
        
        # Calculate chord length
        chord_length = 2 * RADIUS * math.sin(angle_rad / 2)
        
        # Calculate end point using chord
        end_x = chord_length * math.cos(angle_rad / 2)
        end_y = chord_length * math.sin(angle_rad / 2)
        
        return TrackGeometry(
            start=Point(0, 0),
            end=Point(end_x, end_y),
            angle=ANGLE
        )
    
    def transform(self, position: Point, rotation: float) -> 'TrackGeometry':
        """Returns a new geometry transformed by position and rotation."""
        # Convert rotation to radians
        rot_rad = math.radians(rotation)
        
        # Create rotation matrix
        cos_a = math.cos(rot_rad)
        sin_a = math.sin(rot_rad)
        
        # Rotate and translate start point
        new_start_x = (self.start.x * cos_a - self.start.y * sin_a + position.x)
        new_start_y = (self.start.x * sin_a + self.start.y * cos_a + position.y)
        
        # Rotate and translate end point
        new_end_x = (self.end.x * cos_a - self.end.y * sin_a + position.x)
        new_end_y = (self.end.x * sin_a + self.end.y * cos_a + position.y)
        
        return TrackGeometry(
            start=Point(new_start_x, new_start_y),
            end=Point(new_end_x, new_end_y),
            angle=(self.angle + rotation) % 360  # Keep angle between 0 and 360
        )

class TrackType(str, Enum):
    STRAIGHT = "straight"
    CURVED = "curved"
    SWITCH = "switch"

@dataclass
class TrackPiece:
    type: TrackType
    geometry: TrackGeometry
    connections: List[str]
    id: Optional[str] = None

class LayoutGenerator:
    def __init__(self):
        self.STRAIGHT_LENGTH = 16  # studs
        self.CURVE_RADIUS = 40     # studs
        self.CURVE_ANGLE = 22.5    # degrees
        self.TRACK_WIDTH = 8       # studs (including ties)
        self.PARALLEL_SPACING = 8   # studs between parallel tracks
        
    def generate_oval(self) -> List[TrackGeometry]:
        """Generate a basic oval layout."""
        pieces = []
        current_pos = Point(0, 0)
        cumulative_rotation = 0
        
        # First curved section (8 pieces for 180 degrees)
        for i in range(8):
            curve = TrackGeometry.from_curve()
            transformed = curve.transform(current_pos, cumulative_rotation)
            pieces.append(transformed)
            
            # Update position and rotation for next piece
            current_pos = transformed.end
            cumulative_rotation += curve.angle
        
        # First straight section
        straight = TrackGeometry.from_straight()
        transformed = straight.transform(current_pos, cumulative_rotation)
        pieces.append(transformed)
        current_pos = transformed.end
        
        # Second curved section
        for i in range(8):
            curve = TrackGeometry.from_curve()
            transformed = curve.transform(current_pos, cumulative_rotation)
            pieces.append(transformed)
            current_pos = transformed.end
            cumulative_rotation += curve.angle
        
        # Second straight section to close the loop
        straight = TrackGeometry.from_straight()
        transformed = straight.transform(current_pos, cumulative_rotation)
        pieces.append(transformed)
        
        return pieces

    def validate_layout(self, pieces: List[TrackGeometry], tolerance: float = 0.1) -> bool:
        """Validate that a layout forms a closed loop."""
        if not pieces:
            return False
            
        print("\nValidating layout connections...")
        
        # Check that each piece connects to the next
        for i in range(len(pieces)-1):
            current = pieces[i]
            next_piece = pieces[i+1]
            
            # Check position connection
            distance = current.end.distance_to(next_piece.start)
            print(f"Distance between pieces {i} and {i+1}: {distance:.2f}")
            
            if distance > tolerance:
                print(f"Gap found between piece {i} and {i+1}")
                print(f"End: ({current.end.x:.2f}, {current.end.y:.2f})")
                print(f"Start: ({next_piece.start.x:.2f}, {next_piece.start.y:.2f})")
                return False
            
            # Check angle alignment
            angle_diff = abs((current.angle % 360) - (next_piece.angle % 360))
            if angle_diff > tolerance and abs(360 - angle_diff) > tolerance:
                print(f"Angle misalignment between pieces {i} and {i+1}")
                print(f"Angle difference: {angle_diff:.2f}")
                return False
        
        # Check that the layout closes (last piece connects to first)
        closure_distance = pieces[-1].end.distance_to(pieces[0].start)
        print(f"Layout closure distance: {closure_distance:.2f}")
        
        if closure_distance > tolerance:
            print("Layout doesn't close")
            print(f"Last piece end: ({pieces[-1].end.x:.2f}, {pieces[-1].end.y:.2f})")
            print(f"First piece start: ({pieces[0].start.x:.2f}, {pieces[0].start.y:.2f})")
            return False
            
        return True

    def convert_to_layout(self, pieces: List[TrackGeometry]) -> Optional[Dict]:
        """Convert geometric representation to layout format."""
        if not self.validate_layout(pieces):
            return None
            
        layout_pieces = []
        connections = []
        
        # Convert pieces to layout format
        for i, piece in enumerate(pieces):
            is_curved = abs(piece.angle) > 0.1
            piece_id = f"{'curve' if is_curved else 'straight'}_{i}"
            
            # Store each piece with its absolute position and angle
            layout_pieces.append({
                "id": piece_id,
                "type": "curved" if is_curved else "straight",
                "length": self.STRAIGHT_LENGTH,
                "connections": ["left", "right"],
                "position": [piece.start.x, piece.start.y],
                "rotation": piece.angle
            })
            
            # Connect to previous piece
            if i > 0:
                prev_id = f"{'curve' if abs(pieces[i-1].angle) > 0.1 else 'straight'}_{i-1}"
                connections.append({
                    "piece1_id": prev_id,
                    "piece2_id": piece_id,
                    "point1": "right",
                    "point2": "left"
                })
        
        # Close the loop
        connections.append({
            "piece1_id": f"{'curve' if abs(pieces[-1].angle) > 0.1 else 'straight'}_{len(pieces)-1}",
            "piece2_id": f"{'curve' if abs(pieces[0].angle) > 0.1 else 'straight'}_0",
            "point1": "right",
            "point2": "left"
        })
        
        return {
            "pieces": layout_pieces,
            "connections": connections
        }

    def generate_layouts(self, available_pieces: List[Dict]) -> List[Dict]:
        """Generate possible layouts from available pieces."""
        print("\n=== Starting Layout Generation ===")
        
        # Process available pieces
        piece_counts = {}
        for piece in available_pieces:
            piece_counts[piece["type"]] = piece["count"]
            
        print(f"Available pieces: {piece_counts}")
        
        # Try to generate an oval layout
        if piece_counts.get("curved", 0) >= 16 and piece_counts.get("straight", 0) >= 2:
            print("\nAttempting to generate oval layout...")
            geometric_pieces = self.generate_oval()
            
            print("\nValidating geometry...")
            if self.validate_layout(geometric_pieces):
                print("Geometry is valid")
                layout = self.convert_to_layout(geometric_pieces)
                if layout:
                    print("Successfully created oval layout")
                    return [layout]
        
        print("Could not generate any valid layouts")
        return []

app = FastAPI(title="LEGO Track Layout Service")
layout_generator = LayoutGenerator()

@app.post("/api/generate-layouts")
async def generate_layouts(available_pieces: List[Dict]):
    try:
        layouts = layout_generator.generate_layouts(available_pieces)
        return {
            "success": True,
            "layouts": layouts,
            "count": len(layouts)
        }
    except Exception as e:
        print(f"Error in generate_layouts: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/validate-layout")
async def validate_layout(layout: Dict):
    try:
        print("\n=== Validating Layout ===")
        print(f"Layout has {len(layout['pieces'])} pieces and {len(layout['connections'])} connections")
        
        # Convert layout pieces to geometric representation
        geometric_pieces = []
        for piece in layout['pieces']:
            if piece['type'] == 'curved':
                geom = TrackGeometry.from_curve()
            else:
                geom = TrackGeometry.from_straight()
                
            # Transform to position and rotation
            pos = Point(piece['position'][0], piece['position'][1])
            geom = geom.transform(pos, piece['rotation'])
            geometric_pieces.append(geom)
        
        # Validate using geometric validator
        is_valid = layout_generator.validate_layout(geometric_pieces)
        
        message = "Layout forms a valid closed loop" if is_valid else "Layout does not form a closed loop"
        print(f"Validation result: {is_valid}")
        print(f"Message: {message}")
        print("=== Validation Complete ===\n")
        
        return {
            "valid": is_valid,
            "message": message
        }
    except Exception as e:
        print(f"Error in validate_layout: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    import sys
    try:
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    except KeyboardInterrupt:
        print("\nShutting down server...")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting server: {str(e)}")
        sys.exit(1)