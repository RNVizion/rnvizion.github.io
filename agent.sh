# (run inside the rnvizion.github.io Codespace)
cd /workspaces
git clone https://github.com/RNVizion/publishing-agent.git
cd publishing-agent
pip install -q -r requirements.txt 
# non-destructive proof: dry-run an existing post
python agent.py "Publish the post at blog/squish/ as a dry run."
