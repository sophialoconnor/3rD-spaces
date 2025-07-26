#!/usr/bin/env python3

import requests
import sys
import json
import time
from datetime import datetime

class DublinCulturalEventsAPITester:
    def __init__(self, base_url="https://1426ba6a-adbd-45db-b0c8-5f72b4765409.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=30):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else self.api_url
        
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = self.session.get(url, timeout=timeout)
            elif method == 'POST':
                response = self.session.post(url, json=data, timeout=timeout)
            else:
                raise ValueError(f"Unsupported method: {method}")

            success = response.status_code == expected_status
            
            if success:
                try:
                    response_data = response.json()
                    details = f"- Status: {response.status_code}"
                    if isinstance(response_data, dict) and 'message' in response_data:
                        details += f" - Message: {response_data['message']}"
                    elif isinstance(response_data, list):
                        details += f" - Items: {len(response_data)}"
                    self.log_test(name, True, details)
                    return True, response_data
                except json.JSONDecodeError:
                    self.log_test(name, True, f"- Status: {response.status_code} (Non-JSON response)")
                    return True, response.text
            else:
                error_details = f"- Expected {expected_status}, got {response.status_code}"
                try:
                    error_data = response.json()
                    if 'detail' in error_data:
                        error_details += f" - Error: {error_data['detail']}"
                except:
                    error_details += f" - Response: {response.text[:200]}"
                self.log_test(name, False, error_details)
                return False, {}

        except requests.exceptions.Timeout:
            self.log_test(name, False, f"- Request timed out after {timeout}s")
            return False, {}
        except requests.exceptions.ConnectionError:
            self.log_test(name, False, "- Connection error")
            return False, {}
        except Exception as e:
            self.log_test(name, False, f"- Exception: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test the root API endpoint"""
        return self.run_test("Root API Endpoint", "GET", "", 200)

    def test_scrape_status(self):
        """Test scraping status endpoint"""
        success, data = self.run_test("Scrape Status", "GET", "scrape/status", 200)
        if success and isinstance(data, dict):
            print(f"   📊 Status: {data.get('status', 'unknown')}")
            print(f"   📊 Scraped Count: {data.get('scraped_count', 0)}")
            print(f"   📊 Last Scraped: {data.get('last_scraped', 'Never')}")
        return success, data

    def test_trigger_scrape(self):
        """Test triggering scrape"""
        return self.run_test("Trigger Scrape", "POST", "scrape", 200)

    def test_search_functionality(self):
        """Test search functionality with various queries"""
        test_queries = [
            {"query": "music", "limit": 5},
            {"query": "art", "limit": 3},
            {"query": "events", "limit": 10},
            {"query": "dublin", "limit": 5}
        ]
        
        all_passed = True
        for query_data in test_queries:
            query_name = f"Search '{query_data['query']}'"
            success, data = self.run_test(query_name, "POST", "search", 200, query_data)
            
            if success and isinstance(data, list):
                print(f"   📊 Results found: {len(data)}")
                if len(data) > 0:
                    sample_result = data[0]
                    print(f"   📊 Sample result: {sample_result.get('title', 'No title')[:50]}...")
                    print(f"   📊 Relevance score: {sample_result.get('relevance_score', 0):.2f}")
            
            if not success:
                all_passed = False
        
        return all_passed

    def test_content_stats(self):
        """Test content statistics endpoint"""
        success, data = self.run_test("Content Stats", "GET", "content/stats", 200)
        if success and isinstance(data, dict):
            print(f"   📊 Total articles: {data.get('total_articles', 0)}")
            if 'by_type' in data:
                print(f"   📊 Content types: {list(data['by_type'].keys())}")
            if 'by_source' in data:
                print(f"   📊 Sources: {len(data['by_source'])} websites")
        return success, data

    def test_recent_content(self):
        """Test recent content endpoint"""
        success, data = self.run_test("Recent Content", "GET", "content/recent", 200)
        if success and isinstance(data, list):
            print(f"   📊 Recent items: {len(data)}")
            if len(data) > 0:
                sample_item = data[0]
                print(f"   📊 Latest: {sample_item.get('title', 'No title')[:50]}...")
        return success, data

    def test_search_edge_cases(self):
        """Test search with edge cases"""
        edge_cases = [
            {"query": "", "limit": 5},  # Empty query
            {"query": "nonexistentquery12345", "limit": 5},  # Non-existent query
            {"query": "a", "limit": 1},  # Single character
            {"query": "music", "limit": 100}  # Large limit
        ]
        
        all_passed = True
        for i, query_data in enumerate(edge_cases):
            query_name = f"Search Edge Case {i+1}"
            success, data = self.run_test(query_name, "POST", "search", 200, query_data, timeout=10)
            if not success:
                all_passed = False
        
        return all_passed

    def run_comprehensive_test(self):
        """Run all tests in sequence"""
        print("🚀 Starting Dublin Cultural Events Search Engine API Tests")
        print("=" * 60)
        
        # Test basic connectivity
        print("\n📡 CONNECTIVITY TESTS")
        self.test_root_endpoint()
        
        # Test scraping functionality
        print("\n🕷️ SCRAPING TESTS")
        scrape_status_success, scrape_status = self.test_scrape_status()
        
        # If no data has been scraped, trigger scraping
        if scrape_status_success and scrape_status.get('scraped_count', 0) == 0:
            print("\n⚠️  No data found, triggering scrape...")
            self.test_trigger_scrape()
            print("   ⏳ Waiting 10 seconds for scraping to start...")
            time.sleep(10)
            self.test_scrape_status()
        
        # Test content endpoints
        print("\n📊 CONTENT TESTS")
        self.test_content_stats()
        self.test_recent_content()
        
        # Test search functionality
        print("\n🔍 SEARCH TESTS")
        self.test_search_functionality()
        self.test_search_edge_cases()
        
        # Final results
        print("\n" + "=" * 60)
        print(f"📊 FINAL RESULTS: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed! API is working correctly.")
            return 0
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed.")
            return 1

def main():
    """Main test execution"""
    tester = DublinCulturalEventsAPITester()
    return tester.run_comprehensive_test()

if __name__ == "__main__":
    sys.exit(main())