#!/bin/bash
TEX_DIR="tex_sources"

# Use the patched sdaps checkout (adds OCR-training capture/export support)
# rather than the system-wide "sdaps" (an unpatched v1.9.13 install).
SDAPS="python3 $HOME/PaperQuestionnaires/sdaps/sdaps.py"

mkdir -p projects
mkdir -p sortedSurveys
for tex in "$TEX_DIR"/*.tex; do
    echo "Processing $tex"
    filename=$(basename "$tex" .tex)
    project="${filename%.tex}"

    echo "-----"
    echo "Looking at: $project"

    if [ ! -d "projects/$project" ]; then
        echo "Creating project for $project"
        cd projects && $SDAPS setup tex "$project" "../$tex"
        cd ..
    else
        echo "Project for $project already exists, skipping."
    fi

    if [ ! -d "sortedSurveys/$project" ]; then
        echo "Creating sorted survey for $project"
        mkdir -p "sortedSurveys/$project"
    else
        echo "Sorted survey for $project already exists, skipping."
    fi
done

echo "-----"
echo "Completed"
