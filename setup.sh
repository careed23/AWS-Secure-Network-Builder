"""
#!/bin/bash

echo "🚀 Setting up AWS Secure Network Builder..."

# Create directory structure
mkdir -p modules configs logs output tests

# Create __init__.py for modules
touch modules/__init__.py

# Create empty test file
touch tests/__init__.py

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install boto3 pyyaml

# Check AWS CLI
if command -v aws &> /dev/null; then
    echo "✅ AWS CLI found"
    
    # Check if configured
    if aws sts get-caller-identity &> /dev/null; then
        echo "✅ AWS credentials configured"
    else
        echo "⚠️  AWS credentials not configured. Run 'aws configure'"
    fi
else
    echo "⚠️  AWS CLI not found. Please install it first."
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Configure AWS credentials: aws configure"
echo "2. Edit configs/prod-vpc.yaml with your settings"
echo "3. Run: python3 builder.py --config configs/prod-vpc.yaml"
"""
