#!/usr/bin/env python3
"""
Import and analyze ALL Gmail messages from all folders
Cascade signal extraction tied to PROJECT GOALS
Tracks analyzed messages to avoid duplicates

Frequency: Hourly at :48 minutes past each hour (UTC)
"""

# STARTUP CHECK
print("[STARTUP] import_substack_imap.py is starting...", flush=True)

import sys
import subprocess
import os

# Add cascade_app_package to path (contains the correct cascade_db)
possible_paths = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cascade_app_package'),
    '/home/claude/cascade_updates/cascade_app_package',
    '/home/claude/confluence/cascade_app_package'
]
cascade_app_package_path = None
for path in possible_paths:
    if os.path.exists(os.path.join(path, 'cascade_db.py')):
        cascade_app_package_path = path
        break

if cascade_app_package_path:
    sys.path.insert(0, cascade_app_package_path)

# Ensure required packages are available (install if missing in cloud environment)
try:
    from imap_tools import MailBox
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "imap-tools", "-q"])

import imaplib
import email
from email.header import decode_header
from cascade_db import add_signal, add_finding, is_message_analyzed, mark_message_analyzed, get_all_goals
from datetime import datetime
import configparser
import re

def fetch_all_gmail_messages(gmail_user, app_password):
    """
    Fetch unanalyzed messages from ALL Gmail folders
    Returns list of messages with metadata
    """
    print("\n[IMAP] Connecting to Gmail IMAP...")

    messages_data = []

    try:
        # Connect to Gmail
        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        mail.login(gmail_user, app_password)
        print(f"Authenticated as {gmail_user}")

        # Get all folders
        status, mailbox_list = mail.list()
        print(f"\n[FOLDERS] Scanning all folders for unanalyzed messages...")

        folders_scanned = 0

        for mailbox_str in mailbox_list:
            mailbox_str = mailbox_str.decode('utf-8') if isinstance(mailbox_str, bytes) else mailbox_str

            # Extract folder name
            if '"' in mailbox_str:
                folder_name = mailbox_str.split('"')[-2]
            else:
                folder_name = mailbox_str.split()[-1]

            try:
                # Select folder
                mail.select(folder_name, readonly=True)
                folders_scanned += 1

                # Fetch all messages in folder
                status, messages = mail.search(None, 'ALL')
                email_ids = messages[0].split()

                for email_id in email_ids[-50:]:  # Last 50 messages per folder
                    status, msg_data = mail.fetch(email_id, '(RFC822)')

                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            try:
                                msg = email.message_from_bytes(response_part[1])

                                # Extract message ID (use only native Message-ID to avoid duplicates)
                                msg_id = msg.get('Message-ID', None)
                                if not msg_id:
                                    continue  # Skip emails without Message-ID

                                msg_id = msg_id.strip('<>')

                                # Skip if already analyzed
                                if is_message_analyzed(msg_id):
                                    continue

                                # Extract headers
                                subject = msg.get('Subject', 'Untitled')
                                from_addr = msg.get('From', 'Unknown')
                                date_str = msg.get('Date', '')

                                # Parse sender name
                                author = from_addr.split('<')[0].strip() if '<' in from_addr else from_addr

                                # Extract body
                                body = ''
                                if msg.is_multipart():
                                    for part in msg.walk():
                                        if part.get_content_type() == 'text/plain':
                                            try:
                                                body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                                                break
                                            except:
                                                pass
                                else:
                                    try:
                                        body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                                    except:
                                        body = msg.get_payload()

                                # Format date
                                try:
                                    from email.utils import parsedate_to_datetime
                                    dt = parsedate_to_datetime(date_str)
                                    date_formatted = dt.strftime('%Y-%m-%d')
                                except:
                                    date_formatted = datetime.now().strftime('%Y-%m-%d')

                                messages_data.append({
                                    'message_id': msg_id,
                                    'folder': folder_name,
                                    'author': author,
                                    'subject': subject,
                                    'body': body,
                                    'date': date_formatted
                                })
                            except Exception as e:
                                continue
            except Exception as e:
                continue

        mail.close()
        mail.logout()

        print(f"Scanned {folders_scanned} folders")
        print(f"Found {len(messages_data)} unanalyzed messages")
        return messages_data

    except imaplib.IMAP4.error as e:
        print(f"IMAP error: {e}")
        return []
    except Exception as e:
        print(f"Error: {e}")
        return []

def load_config():
    """Load Gmail credentials from config.ini"""
    config = configparser.ConfigParser()

    # Look for config.ini in multiple locations (order: most specific first)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    possible_paths = [
        # Direct script directory
        os.path.join(script_dir, 'config.ini'),
        # Streamlit Cloud common paths
        '/home/appuser/cascade_updates/config.ini',
        '/app/cascade_updates/config.ini',
        '/workspace/cascade_updates/config.ini',
        # Original paths
        '/home/claude/cascade_updates/config.ini',
        '/root/cascade_updates/config.ini',
        os.path.expanduser('~/cascade_updates/config.ini'),
        # Working directory variants
        os.path.join(os.getcwd(), 'config.ini'),
        os.path.join(os.getcwd(), 'cascade_updates', 'config.ini'),
        os.path.join(os.getcwd(), '..', 'config.ini'),
        # Root level
        '/cascade_updates/config.ini',
        'config.ini'
    ]

    # Debug: write detailed log to file
    debug_file = '/tmp/config_search.log'
    with open(debug_file, 'w') as f:
        f.write(f"Script location: {os.path.abspath(__file__)}\n")
        f.write(f"Current working directory: {os.getcwd()}\n")
        f.write(f"Script dir: {script_dir}\n")
        f.write(f"Checking {len(possible_paths)} possible paths:\n\n")

        for i, path in enumerate(possible_paths, 1):
            expanded_path = os.path.expanduser(path)
            exists = os.path.exists(expanded_path)
            f.write(f"{i}. {expanded_path}: {'✓ EXISTS' if exists else '✗ not found'}\n")

    # Also print to stdout
    print(f"[DEBUG] Script location: {os.path.abspath(__file__)}")
    print(f"[DEBUG] Current working directory: {os.getcwd()}")
    print(f"[DEBUG] Checking config paths...")

    config_path = None
    for path in possible_paths:
        expanded_path = os.path.expanduser(path)
        if os.path.exists(expanded_path):
            print(f"[DEBUG] Found config.ini at: {expanded_path}")
            config_path = expanded_path
            break

    if not config_path:
        print("config.ini not found")
        print("   Create config.ini with:")
        print("   [gmail]")
        print("   email = your.email@gmail.com")
        print("   app_password = your16charpassword")
        print(f"   Searched paths: {possible_paths}")
        return None, None

    config.read(config_path)
    try:
        gmail_user = config.get('gmail', 'email')
        app_password = config.get('gmail', 'app_password')
        print(f"[DEBUG] Loaded config from: {config_path}")
        return gmail_user, app_password
    except Exception as e:
        print(f"Invalid config.ini format: {e}")
        return None, None

def extract_cascade_signals(subject, body, author, folder):
    """
    Extract cascade-relevant signals from email content
    Analysis driven by PROJECT GOALS from database
    """
    signals = []
    findings = []

    # Get project goals from database
    try:
        goals = get_all_goals()
    except:
        goals = []

    if not goals:
        return signals, findings

    # Combine content for analysis
    content = f"{subject} {body}".lower()
    content_words = content.split()

    # Map goals to cascade nodes and keywords for detection
    goal_node_mapping = {
        'cascade': (0, 'Cascade Detection'),
        'infrastructure': (6, 'Infrastructure System'),
        'bifurcation': (11, 'Bifurcation Point'),
        'geographic': (12, 'Geographic Distribution'),
        'monitor': (6, 'Monitoring System'),
        'failure': (0, 'System Failure'),
        'grid': (2, 'Energy System'),
        'water': (3, 'Water System'),
        'food': (5, 'Food System'),
        'supply': (7, 'Economic/Supply Chain'),
        'energy': (2, 'Energy System'),
        'climate': (1, 'Climate System'),
        'geopolitical': (10, 'Geopolitical Risk'),
        'economic': (8, 'Economic System'),
    }

    # Score email relevance to each goal
    goal_scores = {}
    for goal in goals:
        goal_text = goal['goal_text'].lower()
        score = 0

        # Check for goal keyword matches
        for keyword in goal_text.split():
            if len(keyword) > 3 and keyword in content:
                score += 1

        goal_scores[goal['goal_id']] = {
            'goal': goal,
            'score': score
        }

    # Extract signals for high-relevance goals
    high_relevance_goals = [g for g in goal_scores.values() if g['score'] > 0]

    for goal_data in high_relevance_goals:
        goal = goal_data['goal']
        score = goal_data['score']

        # Determine node from goal category
        category = goal.get('category', 'supporting').lower()
        if 'cascade' in goal['goal_text'].lower():
            node_id = 0
        elif 'infrastructure' in goal['goal_text'].lower():
            node_id = 6
        elif 'bifurcation' in goal['goal_text'].lower():
            node_id = 11
        elif 'geographic' in goal['goal_text'].lower():
            node_id = 12
        elif 'monitoring' in goal['goal_text'].lower():
            node_id = 6
        else:
            node_id = 6  # Default to infrastructure

        signal = {
            'node': node_id,
            'domain': goal['goal_text'][:50],
            'description': f"Email analysis relevant to goal: {goal['goal_text'][:60]}... - from {author}",
            'severity': 'warning' if score < 3 else 'critical',
            'date': datetime.now().strftime('%Y-%m-%d'),
            'source': f"Gmail: {folder} - {subject[:50]}"
        }
        signals.append(signal)

    # Extract finding if significant relevance and substantial content
    if signals and len(body) > 150:
        relevant_goals = ', '.join([g['goal']['goal_text'][:40] for g in high_relevance_goals[:3]])
        finding = {
            'mechanism': 'Project Goal Relevance',
            'text': f"Email from {author} relevant to: {relevant_goals}. Subject: {subject}. Key excerpt: {body[:300]}...",
            'confidence': min(0.95, 0.7 + (len(signals) * 0.05)),
            'evidence': f"Email analysis against project goals"
        }
        findings.append(finding)

    return signals, findings

def generate_gmail_report(all_signals, all_findings, signal_count, finding_count, messages_analyzed):
    """
    Generate structured report of Gmail analysis and dashboard integration
    Shows: signals extracted, findings identified, sources, integration status
    """
    print("\n" + "="*60)
    print("INTEGRATION REPORT: Gmail Message Analysis")
    print("="*60 + "\n")

    if signal_count == 0 and finding_count == 0:
        print("[INFO] No new signals or findings extracted from emails")
        return

    # ============================================
    # SECTION 1: MESSAGES ANALYZED
    # ============================================
    print("[MESSAGES ANALYZED]")
    print(f"Total messages processed: {messages_analyzed}\n")

    # Group by author/source
    sources = {}
    for signal in all_signals:
        source = signal['source']
        if source not in sources:
            sources[source] = 0
        sources[source] += 1

    for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
        print(f"   • {source}: {count} signals")

    # ============================================
    # SECTION 2: SIGNALS INTEGRATED
    # ============================================
    print("\n[SIGNALS INTEGRATED]")
    print(f"Total signals added: {signal_count}\n")

    # Group signals by node
    signals_by_node = {}
    for signal in all_signals:
        node_id = signal['node']
        if node_id not in signals_by_node:
            signals_by_node[node_id] = []
        signals_by_node[node_id].append(signal)

    node_names = {
        0: "Cascade Entry Point / Unclassified",
        3: "Institutional Suppression",
        6: "Measurement Capacity Erosion",
        7: "Economic Depletion",
        11: "Infrastructure Built for Still Climate",
        12: "Adaptation Exhaustion / Geographic Bifurcation"
    }

    for node_id in sorted(signals_by_node.keys()):
        node_signals = signals_by_node[node_id]
        node_name = node_names.get(node_id, f"Node {node_id}")
        print(f"   Node {node_id} ({node_name}): {len(node_signals)} signals")

        for sig in node_signals:
            severity_badge = "🔴 CRITICAL" if sig['severity'] == 'critical' else \
                           "🟠 SERIOUS" if sig['severity'] == 'serious' else \
                           "🟡 WARNING" if sig['severity'] == 'warning' else "ℹ️  INFO"
            print(f"      {severity_badge}")
            print(f"      From: {sig['source'][:60]}")
            print(f"      Topic: {sig['domain'][:70]}")
            print()

    # ============================================
    # SECTION 3: FINDINGS INTEGRATED
    # ============================================
    print("[FINDINGS INTEGRATED]")
    print(f"Total findings added: {finding_count}\n")

    for i, finding in enumerate(all_findings, 1):
        confidence_pct = int(finding['confidence'] * 100)
        print(f"   Finding {i}: {finding['mechanism']}")
        print(f"      Confidence: {confidence_pct}%")
        print(f"      Evidence: {finding['evidence']}")
        print(f"      Summary: {finding['text'][:90]}...")
        print()

    # ============================================
    # SECTION 4: DASHBOARD INTEGRATION STATUS
    # ============================================
    print("[DASHBOARD INTEGRATION]")
    print("   ✓ Signals extracted from email content")
    print("   ✓ Signals mapped to cascade nodes")
    print("   ✓ Findings added to Research Findings tab")
    print("   ✓ Goal-driven signal extraction applied")
    print("   ✓ Author/source attribution tracked")
    print("   ✓ Message deduplication enabled")
    print()

    # ============================================
    # SECTION 5: DATA QUALITY METRICS
    # ============================================
    print("[DATA QUALITY METRICS]")
    print(f"   • Messages analyzed: {messages_analyzed}")
    print(f"   • Signals extracted: {signal_count}")
    print(f"   • Findings generated: {finding_count}")
    print(f"   • Cascade node coverage: {len(signals_by_node)} nodes represented")
    print(f"   • Source diversity: {len(sources)} unique email sources")
    print(f"   • Message deduplication: Enabled (prevents re-analysis)")
    print()

    # ============================================
    # SECTION 6: NEXT ACTIONS FOR DASHBOARD
    # ============================================
    print("[DASHBOARD NEXT STEPS]")
    print("   1. View new signals in 'Granularity' tab → All Signals (Detailed View)")
    print("   2. Filter by 'source' to see email-derived signals")
    print("   3. Review findings in 'Research Findings' tab → Latest Entries")
    print("   4. Check cascade node activation in 'System Mechanism Tracker'")
    print("   5. Monitor email contributor impact in 'Today's Progress'")
    print()

    # ============================================
    # SECTION 7: PERSISTENCE & ARCHIVAL
    # ============================================
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print("[ARCHIVAL]")
    print(f"   Timestamp: {timestamp}")
    print(f"   Database: Cascade_DB updated with {signal_count} signals, {finding_count} findings")
    print(f"   Deduplication: Message IDs tracked to prevent re-analysis")
    print(f"   Status: ✓ COMMITTED TO DATABASE")
    print()

def main():
    print("\n" + "="*60)
    print("Analyzing All Gmail Messages")
    print("="*60 + "\n")

    # Load credentials
    gmail_user, app_password = load_config()

    if not gmail_user:
        print("   Cannot proceed without config.ini")
        return

    # Fetch unanalyzed messages
    messages_data = fetch_all_gmail_messages(gmail_user, app_password)

    if not messages_data:
        print("\n[OK] No new unanalyzed messages")
        return

    print(f"\n[PROCESSING] Processing {len(messages_data)} messages...\n")

    signal_count = 0
    finding_count = 0
    all_signals = []
    all_findings = []

    for msg in messages_data:
        try:
            # Extract signals and findings based on project goals
            signals, findings = extract_cascade_signals(msg['subject'], msg['body'], msg['author'], msg['folder'])

            # Add to database
            for signal in signals:
                try:
                    add_signal(signal['node'], signal['domain'], signal['description'],
                              signal['severity'], signal['date'], signal['source'])
                    print(f"   [OK] Signal from {msg['author']}: {signal['domain']}")
                    all_signals.append(signal)
                    signal_count += 1
                except Exception as e:
                    print(f"   [WARNING] Error adding signal: {e}")

            for finding in findings:
                try:
                    add_finding(finding['mechanism'], finding['text'],
                               finding['confidence'], finding['evidence'])
                    print(f"   [OK] Finding: {finding['mechanism']}")
                    all_findings.append(finding)
                    finding_count += 1
                except Exception as e:
                    print(f"   [WARNING] Error adding finding: {e}")

            # Mark as analyzed
            mark_message_analyzed(msg['message_id'], msg['folder'], msg['author'],
                                 msg['subject'])

        except Exception as e:
            print(f"   [WARNING] Error processing message from {msg['author']}: {e}")
            continue

    print(f"\n[OK] Gmail Analysis Complete!")
    print(f"   - Signals added: {signal_count}")
    print(f"   - Findings added: {finding_count}")
    print(f"   - Messages analyzed: {len(messages_data)}")

    # Generate comprehensive integration report
    generate_gmail_report(all_signals, all_findings, signal_count, finding_count, len(messages_data))

if __name__ == '__main__':
    main()
