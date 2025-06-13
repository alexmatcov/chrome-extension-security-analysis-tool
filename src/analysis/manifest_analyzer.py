import json
import os
from typing import Dict, List, Tuple
import re

class ExtensionRiskScorer:
    def __init__(self):
        # Risk weights based on Google Chrome Enterprise Permission Risk Whitepaper (July 2019)
        # As described in the research paper methodology
        
        self.permission_weights = {
            # Highest Risk (Score: 10) - Broad host permissions
            # Note: Host permissions are handled separately in calculate_host_permission_risk
            
            # High Risk - Critical API Access (Score: 9)
            '<all_urls>': 9,            # Universal URL access - Google "High Risk"
            'nativeMessaging': 9,       # Direct OS program communication - Google "High Risk"
            'debugger': 9,              # "High level super user access" - Google "High Risk"
            
            # High Risk - System Control (Score: 9)
            'cookies': 9,               # Session hijacking potential - Google "High Risk"
            'downloads': 9,             # Script download and execution - Google "High Risk"
            'proxy': 9,                 # "Send user's internet traffic" - Google "High Risk"
            
            # High Risk - Browser Control (Score: 8)
            'tabs': 8,                  # Current URLs and navigation control - Google "High Risk"
            'history': 8,               # Full browsing history access - Google "High Risk"
            'unsafe-eval': 8,           # Remote script execution - Google "High Risk"
            'webRequestBlocking': 8,    # Traffic modification - Google "High Risk"
            'browsingData': 8,          # Clear browsing data - Google "High Risk"
            'privacy': 8,               # "Turn off malware protections" - Google "High Risk"
            
            # High Risk - Device Access (Score: 7)
            'audioCapture': 7,          # "Listen in on user" - Google "High Risk"
            'videoCapture': 7,          # Webcam access - Google "High Risk"
            'tabCapture': 7,            # Screen recording - Google "High Risk"
            'desktopCapture': 7,        # Full desktop screenshots - Google "Medium Risk"
            'pageCapture': 7,           # MHTML capture - Google "High Risk"
            'scripting': 7,             # MV3 equivalent of tabs.executeScript
            
            # Medium Risk - Sensitive Data (Score: 6)
            'bookmarks': 6,             # Personal browsing data - Google "Medium Risk"
            'geolocation': 6,           # Physical location - Google "Medium Risk"
            'webRequest': 6,            # View network requests - Google "Medium Risk"
            'management': 6,            # Extension control - Google "Medium Risk"
            'contentSettings': 6,       # Plugin control - Google "High Risk"
            'webNavigation': 6,         # Website visit tracking - Google "High Risk"
            
            # Medium Risk - Limited Access (Score: 5)
            'activeTab': 5,             # Temporary access - Google "Medium Risk"
            'identity': 5,              # OAuth credentials - Google "Medium Risk"
            'identity.email': 5,        # Email access - Google "Medium Risk"
            'topSites': 5,              # Top visited sites - Google "Medium Risk"
            
            # Medium Risk - User Interaction (Score: 4)
            'clipboardRead': 4,         # Clipboard access - Google "Medium Risk"
            'clipboardWrite': 4,        # Clipboard access - Google "Medium Risk"
            'contextMenus': 4,          # Browser integration - Google "Medium Risk"
            'fileSystem': 4,            # User file access - Google "Medium Risk"
            'fileSystem.directory': 4,  # Directory access - Google "Medium Risk"
            'fileSystem.write': 4,      # File writing - Google "Medium Risk"
            'syncFileSystem': 4,        # Cloud storage sync - Google "Medium Risk"
            
            # Low Risk - System Information (Score: 3)
            'system.memory': 3,         # Hardware information - Google "Low Risk"
            'system.cpu': 3,            # Hardware information - Google "Low Risk"
            'system.display': 3,        # Hardware information - Google "Low Risk"
            'processes': 3,             # Browser process info - Google "Medium Risk"
            'system.storage': 3,        # Storage device info - Google "Medium Risk"
            'unlimitedStorage': 3,      # Storage quota bypass
            
            # Low Risk - Basic Functionality (Score: 2)
            'storage': 2,               # Local extension data - Google "Low Risk"
            'notifications': 2,         # Desktop notifications - Google "Low Risk"
            'sessions': 2,              # Session management - Google "Medium Risk"
            'tts': 2,                   # Text to speech - Google "Medium Risk"
            
            # Low Risk - Minimal Impact (Score: 1)
            'alarms': 1,                # Timer functionality - Google "Low Risk"
            'background': 1,            # Extension runtime - Google "Low Risk"
            'declarativeContent': 1,    # Content-based actions - Google "Low Risk"
            'idle': 1,                  # System idle detection - Google "Low Risk"
            'fontSettings': 1,          # Font management - Google "Low Risk"
            'power': 1,                 # Power management - Google "Low Risk"
            'wallpaper': 1,             # Wallpaper changes - Google "Low Risk"
            'gcm': 1,                   # Google Cloud Messaging - Google "Low Risk"
            'homepage_url': 1,          # Homepage URL - Google "Low Risk"
            
            # Additional permissions from Google's document
            'app.window.fullscreen.overrideEsc': 6,  # Prevent escape - Google "High Risk"
            'content_security_policy': 5,            # CSP manipulation - Google "High Risk"
            'copresence': 5,                         # P2P communication - Google "High Risk"
            'declarativeNetRequest': 6,              # Network blocking - Google "High Risk"
            'declarativeWebRequest': 6,              # Web request control - Google "High Risk"
            'experimental': 6,                       # Experimental APIs - Google "High Risk"
            'hid': 7,                               # Hardware device control - Google "High Risk"
            'socket': 7,                            # Raw connections - Google "High Risk"
            'usb': 7,                               # USB device control - Google "High Risk"
            'usbDevices': 7,                        # USB device access - Google "High Risk"
            'vpnProvider': 7,                       # VPN tunnel - Google "High Risk"
            'web_accessible_resources': 4,          # Web accessible resources - Google "High Risk"
            'externally_connectable': 3,            # External communication
            'mediaGalleries': 2,                    # Media file access - Google "Low Risk"
            'platformKeys': 1,                      # Platform certificates - Google "Low Risk"
            'signedInDevices': 1,                   # Signed-in devices - Google "Low Risk"
        }
    
    def extract_host_permissions(self, manifest: Dict) -> List[str]:
        """Extract host permissions from manifest"""
        hosts = []
        
        # Manifest v2 permissions
        if 'permissions' in manifest:
            for perm in manifest['permissions']:
                if isinstance(perm, str) and ('://' in perm or perm.startswith('*')):
                    hosts.append(perm)
        
        # Manifest v3 host_permissions
        if 'host_permissions' in manifest:
            hosts.extend(manifest['host_permissions'])
            
        return hosts
    
    def calculate_host_permission_risk(self, host_permissions: List[str]) -> int:
        """Calculate risk based on host permissions - following paper methodology"""
        if not host_permissions:
            return 0
            
        total_risk = 0
        
        for host in host_permissions:
            # Broad patterns get score 10 (Highest risk in Google's framework)
            if host in ['<all_urls>', '*://*/*', 'http://*/*', 'https://*/*']:
                total_risk += 10
            elif host.count('*') >= 2:  # Other broad patterns
                total_risk += 8
            elif host.startswith('*://'):
                total_risk += 6
            elif '*' in host:
                total_risk += 4
            else:
                total_risk += 2  # Specific domains
                
        return total_risk
    
    def calculate_permission_risk(self, manifest: Dict) -> Tuple[int, List[str]]:
        """Calculate risk based on declared permissions - additive approach from paper"""
        all_permissions = []
        
        # Collect all permissions
        if 'permissions' in manifest:
            all_permissions.extend([p for p in manifest['permissions'] if isinstance(p, str) and '://' not in p])
        
        if 'optional_permissions' in manifest:
            all_permissions.extend([p for p in manifest['optional_permissions'] if isinstance(p, str)])
            
        # Sum all permission risks (additive approach as per paper)
        total_risk = 0
        risky_permissions = []
        
        for perm in all_permissions:
            risk_score = self.permission_weights.get(perm, 0)
            
            if risk_score > 0:
                total_risk += risk_score
                risky_permissions.append(f"{perm} (Score: {risk_score})")
                
        return total_risk, risky_permissions
    
    def calculate_user_factor(self, user_count) -> float:
        """Calculate user factor as described in the paper"""
        try:
            # Ensure user_count is a number
            if isinstance(user_count, str):
                user_count = int(user_count.replace(',', '').replace(' ', ''))
            elif user_count is None:
                user_count = 0
            
            user_count = int(user_count)
            
            if user_count >= 1000000:
                return 2.0
            elif user_count >= 100000:
                return 1.5
            elif user_count >= 10000:
                return 1.0
            elif user_count >= 1000:
                return 0.5
            else:
                return 0.0
        except (ValueError, TypeError, AttributeError):
            return 0.0
    
    def calculate_rating_factor(self, rating, review_count) -> float:
        """Calculate rating factor as described in the paper"""
        try:
            # Ensure rating and review_count are numbers
            if isinstance(rating, str):
                rating = float(rating.replace(',', '').replace(' ', ''))
            elif rating is None:
                rating = 5.0
                
            if isinstance(review_count, str):
                review_count = int(review_count.replace(',', '').replace(' ', ''))
            elif review_count is None:
                review_count = 0
                
            rating = float(rating)
            review_count = int(review_count)
            
            if rating >= 4.5 and review_count >= 1000:
                return -1.5
            elif rating >= 4.0 and review_count >= 500:
                return -1.0
            elif rating >= 3.5 and review_count >= 100:
                return -0.5
            elif rating < 2.5 or review_count < 10:
                return 1.0
            elif rating < 3.0:
                return 0.5
            else:
                return 0.0
        except (ValueError, TypeError, AttributeError):
            return 0.0
    
    def get_risk_level(self, total_score: float) -> str:
        """Determine risk level based on paper thresholds"""
        if total_score >= 18:
            return "Critical"
        elif total_score >= 12:
            return "High"
        elif total_score >= 6:
            return "Medium"
        elif total_score >= 1:
            return "Low"
        else:
            return "No Risk"
    
    def calculate_total_risk(self, manifest_path: str) -> Tuple[float, Dict]:
        """Calculate total risk score using exact methodology from the paper"""
        try:
            # Handle UTF-8 BOM and encoding issues
            with open(manifest_path, 'r', encoding='utf-8-sig') as f:
                content = f.read().strip()
                
            if not content:
                return 0.0, {}
                
            # Additional BOM cleanup if utf-8-sig didn't catch it
            if content.startswith('\ufeff'):
                content = content[1:]
                
            # Split metadata and manifest
            if '---' in content:
                parts = content.split('---')
                if len(parts) >= 3:
                    metadata_yaml = parts[1].strip()
                    manifest_json = parts[2].strip()
                elif len(parts) == 2:
                    # Only metadata, no manifest
                    return 0.0, {}
                else:
                    metadata_yaml = ""
                    manifest_json = content
            else:
                metadata_yaml = ""
                manifest_json = content
            
            if not manifest_json.strip():
                return 0.0, {}
                
            # Additional cleanup of manifest JSON
            manifest_json = manifest_json.strip()
            if manifest_json.startswith('\ufeff'):
                manifest_json = manifest_json[1:]
            
            # Validate that we have actual JSON content
            if not manifest_json or not (manifest_json.startswith('{') and manifest_json.endswith('}')):
                return 0.0, {}
            
            # Parse manifest JSON with better error handling
            try:
                manifest = json.loads(manifest_json)
            except json.JSONDecodeError as json_error:
                print(f"JSON decode error in {manifest_path}: {json_error}")
                return 0.0, {}
            
            # Validate that manifest is a dictionary
            if not isinstance(manifest, dict):
                return 0.0, {}
            
            # Parse metadata
            metadata = self.parse_simple_metadata(metadata_yaml)
            
            # Calculate risk components following paper methodology
            host_permissions = self.extract_host_permissions(manifest)
            
            permission_risk, risky_permissions = self.calculate_permission_risk(manifest)
            host_risk = self.calculate_host_permission_risk(host_permissions)
            
            # User and rating factors as described in paper
            user_count = metadata.get('user_count', 0)
            rating = metadata.get('rating', 5.0) 
            review_count = metadata.get('rating_count', 0)
            
            # Ensure we have valid values with fallbacks
            try:
                user_count = int(user_count) if user_count is not None else 0
            except (ValueError, TypeError):
                user_count = 0
                
            try:
                rating = float(rating) if rating is not None else 5.0
            except (ValueError, TypeError):
                rating = 5.0
                
            try:
                review_count = int(review_count) if review_count is not None else 0
            except (ValueError, TypeError):
                review_count = 0
            
            user_factor = self.calculate_user_factor(user_count)
            rating_factor = self.calculate_rating_factor(rating, review_count)
            
            # Paper formula: Risk Score = Σ(permission_scores) + User Factor + Rating Factor
            total_risk = permission_risk + host_risk + user_factor + rating_factor
            
            # Additional context flags (not in risk calculation but useful for analysis)
            additional_flags = []
            if self.has_externally_connectable(manifest):
                additional_flags.append("Externally Connectable")
            if self.has_content_scripts(manifest):
                additional_flags.append("Content Scripts")
            if 'web_accessible_resources' in manifest:
                additional_flags.append("Web Accessible Resources")
                
            risk_breakdown = {
                'permission_risk': permission_risk,
                'host_risk': host_risk,
                'user_factor': user_factor,
                'rating_factor': rating_factor,
                'total_risk': round(total_risk, 2),
                'risk_level': self.get_risk_level(total_risk),
                'host_permissions': host_permissions,
                'risky_permissions': risky_permissions,
                'additional_flags': additional_flags,
                'user_count': user_count,
                'rating': rating,
                'review_count': review_count,
                'externally_connectable': self.has_externally_connectable(manifest),
                'content_scripts': self.has_content_scripts(manifest)
            }
            
            return total_risk, risk_breakdown
            
        except FileNotFoundError:
            print(f"File not found: {manifest_path}")
            return 0.0, {}
        except UnicodeDecodeError as e:
            print(f"Unicode decode error in {manifest_path}: {e}")
            return 0.0, {}
        except Exception as e:
            print(f"Unexpected error processing {manifest_path}: {e}")
            return 0.0, {}
    
    def has_externally_connectable(self, manifest: Dict) -> bool:
        """Check if extension allows external website communication"""
        return 'externally_connectable' in manifest
    
    def has_content_scripts(self, manifest: Dict) -> bool:
        """Check if extension injects content scripts"""
        return 'content_scripts' in manifest and len(manifest['content_scripts']) > 0
    
    def parse_simple_metadata(self, metadata_yaml: str) -> Dict:
        """Simple YAML-like metadata parser"""
        metadata = {}
        for line in metadata_yaml.split('\n'):
            if ':' in line and not line.strip().startswith('-'):
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip().strip('"\'')
                
                # Handle specific numeric fields
                if key in ['user_count', 'rating_count']:
                    try:
                        # Remove commas and convert to int
                        clean_value = value.replace(',', '').replace(' ', '')
                        if clean_value.isdigit():
                            metadata[key] = int(clean_value)
                        else:
                            metadata[key] = 0
                    except (ValueError, AttributeError):
                        metadata[key] = 0
                elif key == 'rating':
                    try:
                        # Convert to float, handling various formats
                        clean_value = value.replace(',', '').replace(' ', '')
                        metadata[key] = float(clean_value)
                    except (ValueError, AttributeError):
                        metadata[key] = 5.0  # Default rating if parsing fails
                else:
                    metadata[key] = value
                    
        return metadata
    
    def is_float(self, value: str) -> bool:
        """Check if string can be converted to float"""
        try:
            float(value)
            return True
        except ValueError:
            return False

def analyze_extensions_directory(
    directory_path: str, 
    all_output_file: str = "all_extensions_ranked.json", 
    top_k_output_file: str = "top_10k_risky_extensions.json", 
    top_k: int = 10000
) -> Tuple[List[Tuple[str, float, Dict]], List[Tuple[str, float, Dict]]]:
    """Analyze all extensions using the exact methodology from the research paper"""
    scorer = ExtensionRiskScorer()
    results = []
    errors = []
    
    print(f"Analyzing extensions in {directory_path} using research paper methodology...")
    print("Risk Score = Σ(permission_scores) + User Factor + Rating Factor")
    
    json_files = [f for f in os.listdir(directory_path) if f.endswith('.json')]
    total_files = len(json_files)
    
    for i, filename in enumerate(json_files):
        if i % 1000 == 0:
            print(f"Processed {i}/{total_files} extensions...")
            
        filepath = os.path.join(directory_path, filename)
        extension_id = filename[:-5]  # Remove .json extension
        
        try:
            risk_score, breakdown = scorer.calculate_total_risk(filepath)
            results.append((extension_id, risk_score, breakdown))
        except FileNotFoundError:
            errors.append((extension_id, "File not found"))
        except UnicodeDecodeError as e:
            errors.append((extension_id, f"Unicode decode error: {str(e)}"))
        except json.JSONDecodeError as e:
            errors.append((extension_id, f"JSON decode error: {str(e)}"))
        except Exception as e:
            errors.append((extension_id, f"General error: {str(e)}"))
            if len(errors) <= 10:
                print(f"Error processing {filepath}: {e}")
    
    # Sort by risk score descending
    results.sort(key=lambda x: x[1], reverse=True)
    
    # Get top-k riskiest extensions
    top_k_results = results[:top_k]
    
    print(f"\nAnalysis complete!")
    print(f"Total extensions processed: {total_files}")
    print(f"Total extensions analyzed: {len(results)}")
    print(f"Errors encountered: {len(errors)}")
    
    # Save both complete and top-k results
    save_results_to_file(results, all_output_file, errors, "All Extensions Analysis")
    save_results_to_file(top_k_results, top_k_output_file, errors, f"Top {top_k} Riskiest Extensions")
    
    return results, top_k_results

def save_results_to_file(results: List[Tuple[str, float, Dict]], output_file: str, errors: List[Tuple[str, str]], analysis_type: str):
    """Save analysis results to JSON file"""
    
    # Calculate statistics using paper thresholds
    risk_distribution = {
        "critical_18_plus": len([r for r in results if r[1] >= 18]),
        "high_12_17": len([r for r in results if 12 <= r[1] < 18]),
        "medium_6_11": len([r for r in results if 6 <= r[1] < 12]),
        "low_1_5": len([r for r in results if 1 <= r[1] < 6]),
        "no_risk_0": len([r for r in results if r[1] < 1])
    }
    
    risky_extensions = [r for r in results if r[1] >= 1]
    
    output_data = {
        "analysis_info": {
            "analysis_type": analysis_type,
            "framework": "Research Paper Methodology: Large-Scale Security Risk Evaluation of Chrome Browser Extensions",
            "methodology": "Risk Score = Σ(permission_scores) + User Factor + Rating Factor",
            "based_on": "Google Chrome Enterprise Permission Risk Whitepaper (July 2019)",
            "risk_levels": {
                "Critical (≥18)": "Extensions requiring immediate security review and likely blocking",
                "High (12-17)": "Extensions requiring thorough vetting before deployment", 
                "Medium (6-11)": "Extensions requiring standard security assessment",
                "Low (1-5)": "Extensions with minimal security review needs",
                "No Risk (<1)": "No identified risk factors"
            },
            "user_factor": {
                "≥1M users": "+2.0 points",
                "≥100K users": "+1.5 points",
                "≥10K users": "+1.0 points",
                "≥1K users": "+0.5 points",
                "<1K users": "+0.0 points"
            },
            "rating_factor": {
                "≥4.5 stars + ≥1K reviews": "-1.5 points",
                "≥4.0 stars + ≥500 reviews": "-1.0 points", 
                "≥3.5 stars + ≥100 reviews": "-0.5 points",
                "<2.5 stars or <10 reviews": "+1.0 points",
                "<3.0 stars": "+0.5 points",
                "other": "+0.0 points"
            }
        },
        "analysis_summary": {
            "total_extensions_analyzed": len(results),
            "extensions_with_risk": len(risky_extensions),
            "extensions_with_zero_risk": risk_distribution["no_risk_0"],
            "total_errors": len(errors),
            "highest_risk_score": round(results[0][1], 2) if results else 0,
            "average_risk_score": round(sum(r[1] for r in results) / len(results), 2) if results else 0,
            "average_risk_score_risky_only": round(sum(r[1] for r in risky_extensions) / len(risky_extensions), 2) if risky_extensions else 0
        },
        "risk_distribution": risk_distribution,
        "extensions": []
    }
    
    for i, (ext_id, risk_score, breakdown) in enumerate(results):
        extension_data = {
            "rank": i + 1,
            "extension_id": ext_id,
            "total_risk_score": round(risk_score, 2),
            "risk_level": breakdown.get('risk_level', 'No Risk'),
            "risk_breakdown": {
                "permission_risk": breakdown.get('permission_risk', 0),
                "host_risk": breakdown.get('host_risk', 0),
                "user_factor": breakdown.get('user_factor', 0),
                "rating_factor": breakdown.get('rating_factor', 0)
            },
            "metadata": {
                "user_count": breakdown.get('user_count', 0),
                "rating": breakdown.get('rating', 0),
                "review_count": breakdown.get('review_count', 0)
            },
            "risk_details": {
                "host_permissions": breakdown.get('host_permissions', []),
                "risky_permissions": breakdown.get('risky_permissions', [])[:10],  # Limit to first 10 for readability
                "additional_flags": breakdown.get('additional_flags', [])
            }
        }
        output_data["extensions"].append(extension_data)
    
    # Save to JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    # Save CSV version
    csv_file = output_file.replace('.json', '.csv')
    save_results_to_csv(results, csv_file)
    
    print(f"{analysis_type} saved to {output_file}")
    print(f"CSV version saved to {csv_file}")

def save_results_to_csv(results: List[Tuple[str, float, Dict]], csv_file: str):
    """Save results to CSV format"""
    import csv
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow([
            'Rank', 'Extension_ID', 'Total_Risk_Score', 'Risk_Level',
            'Permission_Risk', 'Host_Risk', 'User_Factor', 'Rating_Factor',
            'User_Count', 'Rating', 'Review_Count',
            'Host_Permissions_Count', 'Risky_Permissions_Count', 'Additional_Flags'
        ])
        
        # Data rows
        for i, (ext_id, risk_score, breakdown) in enumerate(results):
            writer.writerow([
                i + 1,
                ext_id,
                round(risk_score, 2),
                breakdown.get('risk_level', 'No Risk'),
                breakdown.get('permission_risk', 0),
                breakdown.get('host_risk', 0),
                breakdown.get('user_factor', 0),
                breakdown.get('rating_factor', 0),
                breakdown.get('user_count', 0),
                breakdown.get('rating', 0),
                breakdown.get('review_count', 0),
                len(breakdown.get('host_permissions', [])),
                len(breakdown.get('risky_permissions', [])),
                '; '.join(breakdown.get('additional_flags', []))
            ])

# Example usage
if __name__ == "__main__":
    # Analyze extensions using exact research paper methodology
    all_extensions, top_10k_extensions = analyze_extensions_directory(
        "../extensions/manifests-2025-01-10", 
        all_output_file="all_extensions_ranked.json",
        top_k_output_file="top_10k_risky_extensions.json",
        top_k=10000
    )
    
    # Print comprehensive summary following paper results format
    print(f"\n" + "="*80)
    print(f"RESEARCH PAPER METHODOLOGY ANALYSIS SUMMARY")
    print(f"="*80)
    print(f"Formula: Risk Score = Σ(permission_scores) + User Factor + Rating Factor")
    print(f"Total extensions analyzed: {len(all_extensions):,}")
    
    # Risk distribution using paper thresholds
    critical = len([ext for ext in all_extensions if ext[1] >= 18])
    high = len([ext for ext in all_extensions if 12 <= ext[1] < 18])
    medium = len([ext for ext in all_extensions if 6 <= ext[1] < 12])
    low = len([ext for ext in all_extensions if 1 <= ext[1] < 6])
    no_risk = len([ext for ext in all_extensions if ext[1] < 1])
    
    print(f"\nRisk Distribution (Paper Thresholds):")
    print(f"  Critical (≥18):   {critical:,} extensions ({critical/len(all_extensions)*100:.1f}%)")
    print(f"  High (12-17):     {high:,} extensions ({high/len(all_extensions)*100:.1f}%)")
    print(f"  Medium (6-11):    {medium:,} extensions ({medium/len(all_extensions)*100:.1f}%)")
    print(f"  Low (1-5):        {low:,} extensions ({low/len(all_extensions)*100:.1f}%)")
    print(f"  No Risk (<1):     {no_risk:,} extensions ({no_risk/len(all_extensions)*100:.1f}%)")
    
    risky_total = critical + high + medium + low
    print(f"\nTotal extensions with identified risks: {risky_total:,} ({risky_total/len(all_extensions)*100:.1f}%)")
    
    # Score statistics
    if all_extensions:
        max_score = max(ext[1] for ext in all_extensions)
        avg_score = sum(ext[1] for ext in all_extensions) / len(all_extensions)
        print(f"\nScore Statistics:")
        print(f"  Highest score: {max_score:.2f}")
        print(f"  Average score: {avg_score:.2f}")
    
    # User factor impact analysis
    high_users = len([ext for ext in all_extensions if ext[2].get('user_count', 0) >= 100000])
    print(f"\nUser Adoption Impact:")
    print(f"  Extensions with ≥100K users: {high_users:,} ({high_users/len(all_extensions)*100:.1f}%)")
    
    # Rating factor impact analysis  
    well_rated = len([ext for ext in all_extensions if ext[2].get('rating', 0) >= 4.0 and ext[2].get('review_count', 0) >= 500])
    poorly_rated = len([ext for ext in all_extensions if ext[2].get('rating', 0) < 3.0])
    print(f"\nCommunity Validation Impact:")
    print(f"  Well-rated extensions (≥4.0 stars, ≥500 reviews): {well_rated:,}")
    print(f"  Poorly-rated extensions (<3.0 stars): {poorly_rated:,}")
    
    # Show top 10 riskiest extensions
    print(f"\nTop 10 Riskiest Extensions:")
    print(f"-" * 100)
    for i, (ext_id, risk, breakdown) in enumerate(all_extensions[:10]):
        if risk >= 1:
            user_count = breakdown.get('user_count', 0)
            rating = breakdown.get('rating', 0)
            print(f"{i+1:2d}. {ext_id}")
            print(f"    Total Score: {risk:.2f} ({breakdown.get('risk_level', 'Unknown')})")
            print(f"    Components: Permissions({breakdown.get('permission_risk', 0)}) + Host({breakdown.get('host_risk', 0)}) + User({breakdown.get('user_factor', 0)}) + Rating({breakdown.get('rating_factor', 0)})")
            print(f"    Metadata: {user_count:,} users, {rating:.1f} stars, {breakdown.get('review_count', 0)} reviews")
            if breakdown.get('risky_permissions'):
                print(f"    Top Permissions: {', '.join(breakdown.get('risky_permissions', [])[:3])}")
            print()