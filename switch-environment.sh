#!/bin/bash

# AI MCP Toolkit Environment Switcher
echo "🔄 AI MCP Toolkit Environment Switcher"
echo "======================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Check if configs directory exists
if [[ ! -d "configs/templates" ]]; then
    echo -e "${RED}❌ Configuration templates not found!${NC}"
    echo "Please run ./setup.sh first to generate templates."
    exit 1
fi

echo -e "${CYAN}Available environment configurations:${NC}"
echo ""

# List available configurations
counter=1
declare -a configs
for config in configs/templates/.env.*; do
    if [[ -f "$config" ]]; then
        basename_config=$(basename "$config" | sed 's/.env.//')
        echo -e "${YELLOW}[$counter]${NC} $basename_config"
        configs[$counter]=$config
        counter=$((counter + 1))
    fi
done

echo -e "${YELLOW}[$counter]${NC} Auto-detect (recommended)"
configs[$counter]="auto-detect"

echo ""
echo -e "${CYAN}Current configuration:${NC}"
if [[ -f ".env" ]]; then
    # Try to identify current config by comparing with templates
    current_config="Unknown"
    for template in configs/templates/.env.*; do
        if cmp -s ".env" "$template"; then
            current_config=$(basename "$template" | sed 's/.env.//')
            break
        fi
    done
    echo -e "  ${GREEN}✓ Active: $current_config${NC}"
else
    echo -e "  ${RED}❌ No .env file found${NC}"
fi

echo ""
read -p "Select environment configuration [1-$counter]: " choice

if [[ "$choice" -ge 1 && "$choice" -le $counter ]]; then
    selected_config=${configs[$choice]}
    
    if [[ "$selected_config" == "auto-detect" ]]; then
        echo -e "${CYAN}🔍 Auto-detecting environment...${NC}"
        ./setup.sh
    else
        config_name=$(basename "$selected_config" | sed 's/.env.//')
        echo -e "${CYAN}📋 Switching to $config_name configuration...${NC}"
        
        # Backup current .env if it exists
        if [[ -f ".env" ]]; then
            cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
            echo -e "${GREEN}✓ Current .env backed up${NC}"
        fi
        
        # Copy selected template
        cp "$selected_config" .env
        echo -e "${GREEN}✓ Configuration switched to: $config_name${NC}"
        
        # Show what was applied
        echo ""
        echo -e "${CYAN}Applied configuration:${NC}"
        echo -e "  Template: ${YELLOW}$selected_config${NC}"
        echo -e "  Model: ${YELLOW}$(grep OLLAMA_MODEL .env | cut -d'=' -f2)${NC}"
        echo ""
        echo -e "${GREEN}🎉 Environment configuration updated!${NC}"
        echo -e "${YELLOW}Restart your applications to apply the new settings.${NC}"
    fi
else
    echo -e "${RED}❌ Invalid selection${NC}"
    exit 1
fi