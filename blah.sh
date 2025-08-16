     #!/bin/bash
     # Test script to verify the 4 startup issues
     # Run this inside a VM with audio services enabled

     echo "=== VM Startup Issue Verification Script ==="
     echo "Please run this in a VM with audio services enabled"
     echo ""

     # Test 1: yq command error
     echo "1. Testing yq command error patterns:"
     echo "-----------------------------------"
     # Check if the error appears in logs
     if command -v journalctl >/dev/null 2>&1; then
         echo "Checking system logs for yq errors:"
         sudo journalctl -b | grep -i "yq.*File name too long" | tail -5 || echo "No yq errors in journal"
     else
         echo "Checking dmesg for yq errors:"
         dmesg | grep -i "yq.*File name too long" | tail -5 || echo "No yq errors in dmesg"
     fi

     # Try to trigger the error
     echo -e "\nTesting if JSON as filename causes error:"
     LONG_JSON='{"test": "data", "very": "long", "json": "that might be passed as filename"}'
     yq eval '.' "$LONG_JSON" 2>&1 | head -3 || true
     echo ""

     # Test 2: PulseAudio warnings
     echo "2. Testing PulseAudio root warnings:"
     echo "-----------------------------------"
     # Check current user
     echo "Current user: $(whoami)"

     # Check if PulseAudio is installed
     if command -v pulseaudio >/dev/null 2>&1; then
         echo "PulseAudio is installed at: $(which pulseaudio)"

         # Check if running as root
         if [ "$EUID" -eq 0 ]; then
             echo "Running as root - testing pulseaudio commands:"
             pulseaudio --check -v 2>&1 | grep -i "root" || echo "No root warning from --check"
             timeout 2s pulseaudio --start 2>&1 | grep -i "root" || echo "No root warning from --start"
             killall pulseaudio 2>/dev/null || true
         else
             echo "Not running as root - switch to root to test"
         fi

         # Check supervisor config
         echo -e "\nChecking supervisor config for PulseAudio:"
         grep -A5 -B5 "pulseaudio" /etc/supervisor/conf.d/*.conf 2>/dev/null | grep -E "(command|--system)" || echo "No 
     supervisor config found"
     else
         echo "PulseAudio not installed"
     fi
     echo ""

     # Test 3: Missing /etc/modules
     echo "3. Testing /etc/modules issue:"
     echo "------------------------------"
     # Check if file exists
     if [ -f /etc/modules ]; then
         echo "/etc/modules exists with $(wc -l < /etc/modules) lines"
     else
         echo "/etc/modules does NOT exist"
     fi

     # Check if kmod is installed
     if command -v kmod >/dev/null 2>&1; then
         echo "kmod is installed at: $(which kmod)"
     else
         echo "kmod is NOT installed"
     fi

     # Check if alsa packages are installed
     echo -e "\nChecking ALSA packages (which depend on kmod):"
     dpkg -l | grep -E "alsa-(utils|base)" || echo "No ALSA packages found"

     # Try to reproduce the sed error
     echo -e "\nTrying to reproduce sed error:"
     sed 's/test/test2/' /etc/modules 2>&1 || true
     echo ""

     # Test 4: polkitd path issue
     echo "4. Testing polkitd path issue:"
     echo "------------------------------"
     # Check various polkit paths
     echo "Checking polkit binary locations:"
     for path in /usr/libexec/polkitd /usr/lib/polkit-1/polkitd /usr/lib/policykit-1/polkitd; do
         if [ -f "$path" ]; then
             echo "✓ Found: $path"
         else
             echo "✗ Missing: $path"
         fi
     done

     # Check if polkit is installed
     if command -v pkexec >/dev/null 2>&1; then
         echo -e "\npolkit is installed (pkexec found)"
         # Find actual polkitd location
         echo "Searching for polkitd binary:"
         find /usr -name "polkitd" -type f 2>/dev/null | head -5
     else
         echo -e "\npolkit is NOT installed"
     fi

     # Check for polkit service/init scripts
     echo -e "\nChecking for polkit startup scripts:"
     ls -la /etc/init.d/*polkit* 2>/dev/null || echo "No init.d scripts"
     ls -la /lib/systemd/system/*polkit* 2>/dev/null || echo "No systemd units"

     # Check what might be trying to start polkitd
     echo -e "\nChecking processes that might start polkitd:"
     grep -r "polkitd" /etc/init.d/ 2>/dev/null | head -5 || echo "No references in init.d"
     grep -r "polkitd" /etc/supervisor/conf.d/ 2>/dev/null | head -5 || echo "No references in supervisor"

     echo ""
     echo "=== Verification Complete ==="
     echo "Please share the output of this script to confirm the issues"
