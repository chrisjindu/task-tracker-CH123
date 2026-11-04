#!/bin/bash
set -euo pipefail

# ==========================================
# Task Tracker Deployment Script
# ==========================================

APP_NAME="task-tracker"
SERVICE_NAME="task-tracker"
APP_USER="tasktracker"
APP_DIR="/opt/task-tracker"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

# Read the application version directly from app.py
APP_VERSION=$(grep -E '^VERSION[[:space:]]*=' "$REPO_DIR/app.py" \
    | head -n 1 \
    | cut -d '"' -f 2)

# Ensure a version was found
if [[ -z "$APP_VERSION" ]]; then
    echo "ERROR: Could not read VERSION from app.py"
    exit 1
fi

echo "Deploying ${APP_NAME} version ${APP_VERSION}"

# Check that the script is running as root
if [[ "$EUID" -ne 0 ]]; then
    echo "ERROR: Please run this script with sudo."
    exit 1
fi

# Create a dedicated non-login user if it doesn't exist
if ! id "$APP_USER" &>/dev/null; then
    useradd --system --no-create-home \
        --shell /usr/sbin/nologin "$APP_USER"
fi

# Create the application directory
mkdir -p "$APP_DIR"

# Copy application files to the server
cp -r "$REPO_DIR/." "$APP_DIR/"

# Give the application user ownership
chown -R "$APP_USER:$APP_USER" "$APP_DIR"

# Function to install or update the systemd service
install_service() {
    cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=Task Tracker Application
After=network.target

[Service]
Type=simple
User=${APP_USER}
Group=${APP_USER}
WorkingDirectory=${APP_DIR}
ExecStart=/usr/bin/python3 ${APP_DIR}/app.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd and enable the service
    systemctl daemon-reload
    systemctl enable "$SERVICE_NAME"
    systemctl restart "$SERVICE_NAME"
}

# Install and start the application service
install_service

# ==========================================
# Health Check
# ==========================================

echo "Checking application health..."

sleep 3

# Verify that the service is running
if ! systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "ERROR: Task Tracker service is not running."
    systemctl status "$SERVICE_NAME" --no-pager || true
    exit 1
fi

# Verify that the deployed version matches the repository version
DEPLOYED_VERSION=$(grep -E '^VERSION[[:space:]]*=' "$APP_DIR/app.py" \
    | head -n 1 \
    | cut -d '"' -f 2)

if [[ "$DEPLOYED_VERSION" == "$APP_VERSION" ]]; then
    echo "SUCCESS: Task Tracker version ${APP_VERSION} is live."
    exit 0
else
    echo "ERROR: Version mismatch. Expected ${APP_VERSION}, found ${DEPLOYED_VERSION}."
    exit 1
fi



