"""
Test script for MCP client functionality.

This script demonstrates how to use the MCP client to access
external data sources through standardized MCP servers.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "glih-backend" / "src"))

from glih_backend.config import load_config
from glih_backend.mcp.client import get_mcp_client


async def test_list_resources(mcp_client):
    """Test listing all available resources."""
    print("\n" + "=" * 60)
    print("TEST 1: List All Resources")
    print("=" * 60)
    
    if not mcp_client:
        print("❌ MCP is not enabled in configuration")
        print("   Edit config/glih.toml and set [mcp] enabled = true")
        return False
    
    try:
        resources = await mcp_client.list_resources()
        print(f"✅ Found {len(resources)} resources across all servers")
        
        for resource in resources[:5]:  # Show first 5
            print(f"   - {resource.uri}: {resource.name}")
        
        if len(resources) > 5:
            print(f"   ... and {len(resources) - 5} more")
        
        return True
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_read_shipment(mcp_client):
    """Test reading shipment data from WMS."""
    print("\n" + "=" * 60)
    print("TEST 2: Read Shipment Data")
    print("=" * 60)
    
    if not mcp_client:
        print("❌ MCP is not enabled")
        return False
    
    try:
        shipment_id = "TX-CHI-2025-001"
        print(f"Fetching shipment: {shipment_id}")
        
        shipment = await mcp_client.get_shipment(shipment_id)
        
        if shipment:
            print(f"✅ Shipment retrieved successfully")
            print(f"   ID: {shipment.shipment_id}")
            print(f"   Origin: {shipment.origin}")
            print(f"   Destination: {shipment.destination}")
            print(f"   Product: {shipment.product_type}")
            print(f"   Status: {shipment.status}")
            print(f"   Temperature: {shipment.current_temperature}°C")
            print(f"   Required Range: {shipment.temperature_range}")
            print(f"   ETA: {shipment.eta}")
            return True
        else:
            print(f"❌ Shipment not found")
            return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_read_sensor(mcp_client):
    """Test reading sensor data from IoT."""
    print("\n" + "=" * 60)
    print("TEST 3: Read Sensor Data")
    print("=" * 60)
    
    if not mcp_client:
        print("❌ MCP is not enabled")
        return False
    
    try:
        sensor_id = "TEMP-001"
        print(f"Fetching sensor: {sensor_id}")
        
        sensor = await mcp_client.get_sensor_reading(sensor_id)
        
        if sensor:
            print(f"✅ Sensor reading retrieved successfully")
            print(f"   ID: {sensor.sensor_id}")
            print(f"   Type: {sensor.sensor_type}")
            print(f"   Shipment: {sensor.shipment_id}")
            print(f"   Value: {sensor.value} {sensor.unit}")
            print(f"   Status: {sensor.status}")
            print(f"   Timestamp: {sensor.timestamp}")
            return True
        else:
            print(f"❌ Sensor not found")
            return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_read_document(mcp_client):
    """Test reading document from document storage."""
    print("\n" + "=" * 60)
    print("TEST 4: Read Document")
    print("=" * 60)
    
    if not mcp_client:
        print("❌ MCP is not enabled")
        return False
    
    try:
        doc_id = "SOP-TEMP-BREACH-001"
        print(f"Fetching document: {doc_id}")
        
        doc = await mcp_client.get_document(doc_id)
        
        if doc:
            print(f"✅ Document retrieved successfully")
            print(f"   ID: {doc.document_id}")
            print(f"   Title: {doc.title}")
            print(f"   Type: {doc.document_type}")
            print(f"   Tags: {', '.join(doc.tags)}")
            print(f"   Created: {doc.created_at}")
            print(f"   Content preview: {doc.content[:100] if doc.content else 'N/A'}...")
            return True
        else:
            print(f"❌ Document not found")
            return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_query_sensors(mcp_client):
    """Test querying sensors for a shipment."""
    print("\n" + "=" * 60)
    print("TEST 5: Query Sensors by Shipment")
    print("=" * 60)
    
    if not mcp_client:
        print("❌ MCP is not enabled")
        return False
    
    try:
        shipment_id = "TX-CHI-2025-001"
        print(f"Querying sensors for shipment: {shipment_id}")
        
        sensors = await mcp_client.get_shipment_sensors(shipment_id)
        
        print(f"✅ Found {len(sensors)} sensors")
        for sensor in sensors:
            print(f"   - {sensor.sensor_id} ({sensor.sensor_type}): {sensor.value} {sensor.unit}")
        
        return len(sensors) > 0
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_cache(mcp_client):
    """Test caching functionality."""
    print("\n" + "=" * 60)
    print("TEST 6: Cache Performance")
    print("=" * 60)
    
    if not mcp_client:
        print("❌ MCP is not enabled")
        return False
    
    try:
        import time
        
        shipment_id = "TX-CHI-2025-001"
        
        # First request (no cache)
        start = time.time()
        response1 = await mcp_client.read_resource(f"wms://shipments/{shipment_id}", use_cache=False)
        time1 = time.time() - start
        
        # Second request (with cache)
        start = time.time()
        response2 = await mcp_client.read_resource(f"wms://shipments/{shipment_id}", use_cache=True)
        time2 = time.time() - start
        
        print(f"✅ Cache test completed")
        print(f"   First request (no cache): {time1*1000:.2f}ms")
        print(f"   Second request (cached): {time2*1000:.2f}ms")
        if time2 > 0:
            print(f"   Speedup: {time1/time2:.1f}x faster")
        
        return response1.success and response2.success
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("MCP CLIENT TEST SUITE")
    print("=" * 60)
    print("\nMake sure all MCP servers are running:")
    print("  - WMS Server: http://localhost:8080")
    print("  - IoT Server: http://localhost:8081")
    print("  - Docs Server: http://localhost:8082")
    print("\nPress Enter to continue...")
    input()
    
    # Create MCP client once
    config = load_config()
    mcp_client = get_mcp_client(config.get("mcp", {}))
    
    if not mcp_client:
        print("\n❌ MCP is not enabled in configuration")
        print("   Edit config/glih.toml and set [mcp] enabled = true")
        print("   Also ensure each server has enabled = true")
        return
    
    tests = [
        ("List Resources", test_list_resources),
        ("Read Shipment", test_read_shipment),
        ("Read Sensor", test_read_sensor),
        ("Read Document", test_read_document),
        ("Query Sensors", test_query_sensors),
        ("Cache Performance", test_cache),
    ]
    
    results = []
    try:
        for name, test_func in tests:
            try:
                result = await test_func(mcp_client)
                results.append((name, result))
            except Exception as e:
                print(f"\n❌ Test '{name}' crashed: {e}")
                results.append((name, False))
    finally:
        # Close client after all tests
        await mcp_client.close()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 All tests passed! MCP integration is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        print("\nCommon issues:")
        print("  1. MCP servers not running (start with: python mcp-servers/*.py)")
        print("  2. MCP not enabled in config/glih.toml")
        print("  3. Network connectivity issues")


if __name__ == "__main__":
    asyncio.run(main())
