import asyncio
import aiohttp
import json
from typing import Dict, Any

class LegoTrackAPITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def test_generate_layouts(self) -> Dict[str, Any]:
        """Test the layout generation endpoint."""
        print("\n🚂 Testing layout generation...")
        
        # Sample input with different track pieces
        test_data = [
            {"type": "straight", "count": 10},
            {"type": "curved", "count": 16},
            {"type": "switch", "count": 4}
        ]

        print("\nRaw test data:", json.dumps(test_data, indent=2))  # Add this line

        try:
            async with self.session.post(
                f"{self.base_url}/api/generate-layouts",
                json=test_data
            ) as response:
                result = await response.json()
                status = response.status

                print(f"Status Code: {status}")
                if status == 400:
                    print(f"Error detail: {result.get('detail', 'No detail provided')}")
                else:
                    print(f"Number of layouts generated: {result.get('count', 0)}")
                    if result.get('layouts'):
                        print("\nFirst layout details:")
                        layout = result['layouts'][0]
                        print(f"- Number of pieces: {len(layout['pieces'])}")
                        print(f"- Number of connections: {len(layout['connections'])}")
                        print(f"- Piece types: {set(p['type'] for p in layout['pieces'])}")
                    else:
                        print("No layouts were generated")
                        
                return result

        except Exception as e:
            print(f"❌ Error testing layout generation: {str(e)}")
            return {}

    async def test_validate_layout(self) -> Dict[str, Any]:
        """Test the layout validation endpoint."""
        print("\n🔍 Testing layout validation...")

        # Sample valid oval layout
        test_layout = {
            "pieces": [
                {
                    "id": "straight_1",
                    "type": "straight",
                    "length": 16,
                    "connections": ["left", "right"],
                    "position": [0, 0],
                    "rotation": 0
                },
                {
                    "id": "curve_1",
                    "type": "curved",
                    "length": 16,
                    "connections": ["left", "right"],
                    "position": [16, 0],
                    "rotation": 22.5
                }
            ],
            "connections": [
                {
                    "piece1_id": "straight_1",
                    "piece2_id": "curve_1",
                    "point1": "right",
                    "point2": "left"
                }
            ]
        }

        try:
            async with self.session.post(
                f"{self.base_url}/api/validate-layout",
                json=test_layout
            ) as response:
                result = await response.json()
                status = response.status

                print(f"Status Code: {status}")
                print(f"Validation result: {result.get('valid', False)}")
                print(f"Message: {result.get('message', 'No message')}")
                
                return result

        except Exception as e:
            print(f"❌ Error testing layout validation: {str(e)}")
            return {}

    async def run_all_tests(self):
        """Run all API tests."""
        print("🚀 Starting LEGO Track API Tests...")
        
        # Test layout generation
        generation_result = await self.test_generate_layouts()
        
        # If we got a layout, test validation with it
        if generation_result.get('layouts'):
            print("\n🔄 Testing validation with generated layout...")
            first_layout = generation_result['layouts'][0]
            async with self.session.post(
                f"{self.base_url}/api/validate-layout",
                json=first_layout
            ) as response:
                validation_result = await response.json()
                print(f"Validation of generated layout: {validation_result.get('valid', False)}")
                print(f"Message: {validation_result.get('message', 'No message')}")

        # Test validation with sample layout
        await self.test_validate_layout()

        print("\n✨ All tests completed!")

async def main():
    async with LegoTrackAPITester() as tester:
        await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())