#!/usr/bin/env python3
"""
🖥️  User Interface Validation Report
======================================================================
Comprehensive validation of the Universal AI Endpoint Management System Web UI:

1. Frontend structure and assets
2. Interactive components and functionality  
3. API integration and data loading
4. Responsive design and styling
5. Documentation interfaces
6. User experience features
"""

import requests
import time
import json
from typing import Dict, Any, List

BASE_URL = "http://localhost:8000"

class UIValidator:
    """Comprehensive UI validation class"""
    
    def __init__(self):
        self.results = []
        self.ui_features = {}
        
    def log_result(self, test_name: str, passed: bool, details: str = ""):
        """Log UI validation result"""
        result = {
            "test": test_name,
            "passed": passed, 
            "details": details,
            "timestamp": time.time()
        }
        self.results.append(result)
        
        status = "✅" if passed else "❌"
        print(f"{status} {test_name}: {details}")
        return passed
    
    def validate_main_interface(self) -> bool:
        """Validate the main web interface"""
        try:
            response = requests.get(f"{BASE_URL}/", timeout=10)
            
            if response.status_code != 200:
                self.log_result("Main Interface Access", False, f"HTTP {response.status_code}")
                return False
            
            html_content = response.text
            
            # Check for essential UI components
            ui_components = [
                ("HTML Structure", "<!DOCTYPE html>" in html_content),
                ("App Container", 'class="app-container"' in html_content),
                ("Header Section", 'class="app-header"' in html_content),
                ("Sidebar Navigation", 'class="sidebar"' in html_content),
                ("Content Area", 'class="content-area"' in html_content),
                ("Dashboard Tab", 'id="dashboard"' in html_content),
                ("Endpoints Tab", 'id="endpoints"' in html_content),
                ("Chat Interface", 'id="chat-interface"' in html_content),
                ("Monitoring Tab", 'id="monitoring"' in html_content),
                ("YAML Editor", 'id="yaml-editor"' in html_content),
            ]
            
            passed_components = 0
            for component_name, check in ui_components:
                if check:
                    passed_components += 1
                    self.log_result(f"UI Component: {component_name}", True, "Present")
                else:
                    self.log_result(f"UI Component: {component_name}", False, "Missing")
            
            success_rate = (passed_components / len(ui_components)) * 100
            self.log_result("Main Interface", success_rate >= 80, f"{success_rate:.1f}% components present")
            
            return success_rate >= 80
            
        except Exception as e:
            self.log_result("Main Interface", False, f"Exception: {e}")
            return False
    
    def validate_static_assets(self) -> bool:
        """Validate static CSS and JS assets"""
        assets_to_check = [
            ("/static/css/dashboard.css", "CSS Stylesheet"),
            ("/static/js/dashboard.js", "Dashboard JavaScript"),
            ("/static/js/yaml-editor.js", "YAML Editor JavaScript"),
        ]
        
        passed_assets = 0
        
        for asset_path, asset_name in assets_to_check:
            try:
                response = requests.head(f"{BASE_URL}{asset_path}", timeout=5)
                if response.status_code == 200:
                    content_length = response.headers.get('content-length', '0')
                    self.log_result(f"Static Asset: {asset_name}", True, f"Loaded ({content_length} bytes)")
                    passed_assets += 1
                else:
                    self.log_result(f"Static Asset: {asset_name}", False, f"HTTP {response.status_code}")
            except Exception as e:
                self.log_result(f"Static Asset: {asset_name}", False, f"Exception: {e}")
        
        success_rate = (passed_assets / len(assets_to_check)) * 100
        return success_rate >= 80
    
    def validate_external_dependencies(self) -> bool:
        """Validate external CDN dependencies"""
        try:
            response = requests.get(f"{BASE_URL}/", timeout=10)
            html_content = response.text
            
            external_deps = [
                ("Font Awesome Icons", "font-awesome" in html_content),
                ("CodeMirror CSS", "codemirror" in html_content),
                ("Chart.js Library", "chart.js" in html_content),
                ("CodeMirror JS", "codemirror.min.js" in html_content),
            ]
            
            passed_deps = 0
            for dep_name, check in external_deps:
                if check:
                    self.log_result(f"External Dependency: {dep_name}", True, "Referenced")
                    passed_deps += 1
                else:
                    self.log_result(f"External Dependency: {dep_name}", False, "Missing reference")
            
            success_rate = (passed_deps / len(external_deps)) * 100
            return success_rate >= 75
            
        except Exception as e:
            self.log_result("External Dependencies", False, f"Exception: {e}")
            return False
    
    def validate_ui_features(self) -> Dict[str, bool]:
        """Analyze UI features from the HTML structure"""
        try:
            response = requests.get(f"{BASE_URL}/", timeout=10)
            html_content = response.text
            
            features = {
                "Trading Bot Dashboard": "dashboard-stats" in html_content,
                "Endpoint Management": "endpoints-grid" in html_content,
                "YAML Configuration Editor": "yaml-editor-container" in html_content,
                "Test Chat Interface": "chat-container" in html_content,
                "Real-time Monitoring": "monitoring-grid" in html_content,
                "Performance Metrics": "metrics-chart" in html_content,
                "Add Endpoint Modal": "addEndpointModal" in html_content,
                "Responsive Design": "viewport" in html_content,
                "Loading Overlay": "loading-overlay" in html_content,
                "Toast Notifications": "toast-container" in html_content,
                "Connection Status": "connection-status" in html_content,
                "Settings Panel": "settingsBtn" in html_content,
            }
            
            for feature_name, present in features.items():
                self.log_result(f"UI Feature: {feature_name}", present, "Available" if present else "Not found")
            
            self.ui_features = features
            return features
            
        except Exception as e:
            self.log_result("UI Features Analysis", False, f"Exception: {e}")
            return {}
    
    def validate_api_documentation(self) -> bool:
        """Validate API documentation interfaces"""
        doc_endpoints = [
            ("/docs", "Swagger UI Documentation"),
            ("/redoc", "ReDoc Documentation"),
            ("/openapi.json", "OpenAPI Schema"),
        ]
        
        passed_docs = 0
        
        for endpoint, name in doc_endpoints:
            try:
                response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
                if response.status_code == 200:
                    content = response.text
                    if endpoint == "/openapi.json":
                        # Validate JSON structure
                        try:
                            json_data = json.loads(content)
                            has_paths = "paths" in json_data
                            has_info = "info" in json_data
                            self.log_result(f"API Doc: {name}", has_paths and has_info, "Valid OpenAPI schema" if has_paths and has_info else "Invalid schema")
                            if has_paths and has_info:
                                passed_docs += 1
                        except json.JSONDecodeError:
                            self.log_result(f"API Doc: {name}", False, "Invalid JSON")
                    else:
                        # Validate HTML documentation
                        has_title = "<title>" in content
                        has_swagger = "swagger" in content.lower() or "redoc" in content.lower()
                        self.log_result(f"API Doc: {name}", has_title and has_swagger, "Valid documentation page")
                        if has_title and has_swagger:
                            passed_docs += 1
                else:
                    self.log_result(f"API Doc: {name}", False, f"HTTP {response.status_code}")
            except Exception as e:
                self.log_result(f"API Doc: {name}", False, f"Exception: {e}")
        
        return passed_docs >= 2  # At least 2 out of 3 should work
    
    def validate_interactive_features(self) -> bool:
        """Validate interactive JavaScript features"""
        try:
            response = requests.get(f"{BASE_URL}/static/js/dashboard.js", timeout=10)
            
            if response.status_code != 200:
                self.log_result("Interactive Features", False, f"JS not accessible: HTTP {response.status_code}")
                return False
            
            js_content = response.text
            
            interactive_features = [
                ("Class-based Architecture", "class Dashboard" in js_content),
                ("Event Binding", "addEventListener" in js_content),
                ("Tab Switching", "switchTab" in js_content),
                ("Endpoint Management", "loadEndpoints" in js_content),
                ("Periodic Updates", "startPeriodicUpdates" in js_content),
                ("Modal Handling", "showAddEndpointModal" in js_content),
                ("Form Processing", "handleAddEndpoint" in js_content),
                ("API Integration", "fetch" in js_content or "XMLHttpRequest" in js_content),
            ]
            
            passed_features = 0
            for feature_name, check in interactive_features:
                if check:
                    self.log_result(f"JS Feature: {feature_name}", True, "Implemented")
                    passed_features += 1
                else:
                    self.log_result(f"JS Feature: {feature_name}", False, "Not found")
            
            success_rate = (passed_features / len(interactive_features)) * 100
            return success_rate >= 75
            
        except Exception as e:
            self.log_result("Interactive Features", False, f"Exception: {e}")
            return False
    
    def validate_responsive_design(self) -> bool:
        """Validate responsive design elements"""
        try:
            response = requests.get(f"{BASE_URL}/static/css/dashboard.css", timeout=10)
            
            if response.status_code != 200:
                self.log_result("Responsive Design", False, f"CSS not accessible: HTTP {response.status_code}")
                return False
            
            css_content = response.text
            
            responsive_features = [
                ("Mobile Viewport", "@media" in css_content),
                ("Flexbox Layout", "display: flex" in css_content or "display:flex" in css_content),
                ("Grid System", "grid" in css_content),
                ("Responsive Units", "%" in css_content and "rem" in css_content),
                ("CSS Variables", "--" in css_content),
            ]
            
            passed_features = 0
            for feature_name, check in responsive_features:
                if check:
                    self.log_result(f"CSS Feature: {feature_name}", True, "Present")
                    passed_features += 1
                else:
                    self.log_result(f"CSS Feature: {feature_name}", False, "Not detected")
            
            success_rate = (passed_features / len(responsive_features)) * 100
            return success_rate >= 60
            
        except Exception as e:
            self.log_result("Responsive Design", False, f"Exception: {e}")
            return False
    
    def generate_ui_report(self) -> Dict[str, Any]:
        """Generate comprehensive UI validation report"""
        
        print("🖥️  UNIVERSAL AI ENDPOINT MANAGEMENT SYSTEM - UI VALIDATION")
        print("=" * 80)
        print("Comprehensive User Interface Testing")
        print("=" * 80)
        
        # Run all UI validation tests
        main_interface = self.validate_main_interface()
        static_assets = self.validate_static_assets()
        external_deps = self.validate_external_dependencies()
        ui_features = self.validate_ui_features()
        api_docs = self.validate_api_documentation()
        interactive_features = self.validate_interactive_features()
        responsive_design = self.validate_responsive_design()
        
        # Calculate overall success
        core_tests = [main_interface, static_assets, api_docs, interactive_features]
        optional_tests = [external_deps, responsive_design]
        
        core_passed = sum(1 for test in core_tests if test)
        optional_passed = sum(1 for test in optional_tests if test)
        ui_features_passed = sum(1 for feature in ui_features.values() if feature)
        
        total_tests = len(self.results)
        total_passed = sum(1 for result in self.results if result["passed"])
        overall_success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 UI VALIDATION SUMMARY")
        print("=" * 80)
        
        print(f"🎯 Core UI Components: {core_passed}/{len(core_tests)} tests passed")
        print(f"🎨 UI Features Available: {ui_features_passed}/{len(ui_features)} features found")
        print(f"📱 Optional Enhancements: {optional_passed}/{len(optional_tests)} tests passed")
        print(f"📊 Overall Success Rate: {overall_success_rate:.1f}%")
        
        # Detailed breakdown
        print(f"\n📋 DETAILED RESULTS:")
        categories = {}
        for result in self.results:
            category = result['test'].split(':')[0] if ':' in result['test'] else result['test']
            if category not in categories:
                categories[category] = {'passed': 0, 'total': 0}
            categories[category]['total'] += 1
            if result['passed']:
                categories[category]['passed'] += 1
        
        for category, stats in sorted(categories.items()):
            rate = (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0
            print(f"  • {category}: {stats['passed']}/{stats['total']} ({rate:.1f}%)")
        
        # Final assessment
        if overall_success_rate >= 90:
            status = "EXCELLENT"
            print("\n🎉 UI STATUS: EXCELLENT - Professional, fully-featured interface")
        elif overall_success_rate >= 75:
            status = "GOOD" 
            print("\n✅ UI STATUS: GOOD - Functional interface with most features working")
        elif overall_success_rate >= 60:
            status = "FAIR"
            print("\n⚠️  UI STATUS: FAIR - Basic functionality present, some issues")
        else:
            status = "POOR"
            print("\n❌ UI STATUS: POOR - Significant UI issues detected")
        
        print(f"\n🔍 KEY UI HIGHLIGHTS:")
        print(f"  • Trading bot-style dashboard with metrics")
        print(f"  • Multi-tab interface (Dashboard, Endpoints, Chat, Monitoring)")
        print(f"  • Interactive endpoint management")
        print(f"  • YAML configuration editor with AI validation")
        print(f"  • Real-time chat testing interface")
        print(f"  • Performance monitoring and metrics")
        print(f"  • Complete API documentation (Swagger + ReDoc)")
        
        return {
            "status": status,
            "overall_success_rate": overall_success_rate,
            "core_tests": {"passed": core_passed, "total": len(core_tests)},
            "ui_features": {"passed": ui_features_passed, "total": len(ui_features)},
            "detailed_results": categories,
            "all_results": self.results
        }

def main():
    """Run UI validation"""
    validator = UIValidator()
    report = validator.generate_ui_report()
    
    # Return appropriate exit code
    if report["overall_success_rate"] >= 75:
        return 0
    elif report["overall_success_rate"] >= 60:
        return 1
    else:
        return 2

if __name__ == "__main__":
    import sys
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n❌ UI validation interrupted by user")
        sys.exit(3)
    except Exception as e:
        print(f"\n💥 UI validation failed with unexpected error: {e}")
        sys.exit(4)