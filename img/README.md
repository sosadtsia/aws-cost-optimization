# Architecture Diagram

This directory contains the architecture diagram for the AWS Cost Optimization project.

## Viewing the Diagram

The diagram is created using Mermaid, which is supported directly in GitHub markdown. To view the diagram:

1. Open the `architecture.txt` file in this directory
2. Copy the Mermaid diagram code
3. Paste it into any Markdown file (like the main README.md)

## Generating a PNG Version

To generate a PNG version of the diagram:

1. Use the Mermaid CLI:
   ```bash
   npm install -g @mermaid-js/mermaid-cli
   mmdc -i architecture.txt -o architecture.png
   ```

2. Or use the Mermaid Live Editor:
   - Visit https://mermaid.live/
   - Paste the contents of architecture.txt
   - Export as PNG

3. You can also use GitHub to render the diagram directly when viewed on GitHub.com
