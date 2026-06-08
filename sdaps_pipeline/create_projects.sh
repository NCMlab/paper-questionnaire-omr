#!/bin/bash
TEX_DIR="tex_sources"


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
        cd projects && sdaps setup tex "$project" "../$tex"
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
