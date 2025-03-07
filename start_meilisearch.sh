#!/bin/bash
# Start MeiliSearch with proper configuration

echo "Starting MeiliSearch with proper configuration..."
echo "Master Key: 1582d75025acd6f3b8f5445265deb499ee2e843c"
echo "Search Key: e260b7f247952f2b4a3bf78d326f830d04bdeffb38cc621825224c95da599d4e"

# Launch MeiliSearch with configuration
./meilisearch --master-key "1582d75025acd6f3b8f5445265deb499ee2e843c" \
--http-addr "localhost:7700" \
--no-analytics \
--env "development" \
--max-indexing-memory "1 GiB" \
--http-payload-size-limit "104857600"

echo "MeiliSearch stopped." 