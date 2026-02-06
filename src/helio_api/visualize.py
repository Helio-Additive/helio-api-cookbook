"""
Mesh visualization generator for the Helio Additive API.

Generates interactive WebGL/Three.js HTML visualizations from mesh CSV data.
Based on toolpath_visualizer.py patterns for FDM toolpath visualization.
"""

from __future__ import annotations

import csv
import json
import os


def generate_mesh_visualization(
    mesh_csv_path: str,
    output_html_path: str,
    title: str = "Mesh Visualization",
) -> bool:
    """Generate an interactive HTML visualization from mesh CSV data.

    Creates a standalone HTML file with embedded Three.js that provides:
    - 3D WebGL rendering (GPU accelerated)
    - Layer slider with cumulative/single mode
    - Progress slider with play/pause animation
    - Thermal quality coloring (blue -1 → green 0 → red +1)
    - Click-to-inspect element metadata panel
    - Orbit controls (drag to rotate, scroll to zoom, shift+drag to pan)

    Args:
        mesh_csv_path: Path to the mesh CSV file.
        output_html_path: Path to write the output HTML file.
        title: Title for the visualization.

    Returns:
        True on success, False on error.
    """
    if not os.path.isfile(mesh_csv_path):
        print(f"  Error: File not found: {mesh_csv_path}")
        return False

    print(f"  Loading mesh data from {mesh_csv_path}...")

    # Load and process mesh data
    elements = []
    try:
        with open(mesh_csv_path, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Skip rows with missing coordinates
                if not row.get("x1") or not row.get("y1") or not row.get("z1"):
                    continue
                if row.get("x1") == "" or row.get("y1") == "" or row.get("z1") == "":
                    continue

                try:
                    # Handle both 'index' and 'element_index' column names
                    idx_val = row.get("index") or row.get("element_index")
                    element = {
                        "index": int(idx_val) if idx_val and idx_val != "" else -1,
                        "partition": int(row["partition"]) if row.get("partition") and row["partition"] != "" else -1,
                        "layer": int(row["layer"]) if row.get("layer") and row["layer"] != "" else 0,
                        "event": int(row["event"]) if row.get("event") and row["event"] != "" else 0,
                        "temperature": float(row["temperature"]) if row.get("temperature") and row["temperature"] != "" else 0,
                        "fan_speed": float(row["fan_speed"]) if row.get("fan_speed") and row["fan_speed"] != "" else 0,
                        "height": float(row["height"]) if row.get("height") and row["height"] != "" else 0,
                        "width": float(row["width"]) if row.get("width") and row["width"] != "" else 0,
                        "env_temp": float(row["environment_temperature"]) if row.get("environment_temperature") and row["environment_temperature"] != "" else 0,
                        "x": float(row["x1"]),
                        "y": float(row["y1"]),
                        "z": float(row["z1"]),
                        "t": float(row["t1"]) if row.get("t1") and row["t1"] != "" else 0,
                        "quality": float(row["quality"]) if row.get("quality") and row["quality"] != "" else 0,
                    }
                    elements.append(element)
                except (ValueError, KeyError):
                    continue
    except Exception as e:
        print(f"  Error loading mesh CSV: {e}")
        return False

    if not elements:
        print("  Error: No valid elements found in CSV.")
        return False

    # Calculate bounds for centering
    x_vals = [e["x"] for e in elements]
    y_vals = [e["y"] for e in elements]
    z_vals = [e["z"] for e in elements]

    x_center = (min(x_vals) + max(x_vals)) / 2
    y_center = (min(y_vals) + max(y_vals)) / 2
    z_center = (min(z_vals) + max(z_vals)) / 2
    scale = max(max(x_vals) - min(x_vals), max(y_vals) - min(y_vals), max(z_vals) - min(z_vals))
    if scale == 0:
        scale = 1

    # Get layer info
    layers = sorted(set(e["layer"] for e in elements))
    max_layer = max(layers) if layers else 0

    # Build layer data structure with transformed coordinates
    layer_data = []
    for layer in layers:
        layer_elements = [e for e in elements if e["layer"] == layer]

        # Group by partition and sort by time
        partitions = sorted(set(e["partition"] for e in layer_elements))
        segments = []

        for partition in partitions:
            part_elements = sorted(
                [e for e in layer_elements if e["partition"] == partition],
                key=lambda e: e["t"]
            )
            if len(part_elements) < 2:
                continue

            points = []
            qualities = []
            metadata = []

            for elem in part_elements:
                # Transform coordinates: center and scale, swap y/z for Three.js
                points.append([
                    (elem["x"] - x_center) / scale * 100,
                    (elem["z"] - z_center) / scale * 100,  # z -> y in Three.js
                    (elem["y"] - y_center) / scale * 100,  # y -> z in Three.js
                ])
                qualities.append(max(-1, min(1, elem["quality"])))
                metadata.append({
                    "idx": elem["index"],
                    "partition": elem["partition"],
                    "layer": elem["layer"],
                    "event": elem["event"],
                    "temp": elem["temperature"],
                    "fan_speed": elem["fan_speed"],
                    "height": elem["height"],
                    "width": elem["width"],
                    "env_temp": elem["env_temp"],
                    "quality": elem["quality"],
                    "t": elem["t"],
                    "x": elem["x"],
                    "y": elem["y"],
                    "z": elem["z"],
                })

            segments.append({
                "points": points,
                "qualities": qualities,
                "meta": metadata,
            })

        layer_data.append({"layer": layer, "segments": segments})

    total_points = sum(
        sum(len(s["points"]) for s in ld["segments"])
        for ld in layer_data
    )
    print(f"  Processed {len(layers)} layers, {total_points:,} points")

    # Generate HTML
    html_content = _generate_html_template(layer_data, max_layer, total_points, title)

    try:
        with open(output_html_path, "w") as f:
            f.write(html_content)
        print(f"  Saved visualization to: {output_html_path}")
        return True
    except Exception as e:
        print(f"  Error writing HTML: {e}")
        return False


def _generate_html_template(layer_data: list, max_layer: int, total_points: int, title: str) -> str:
    """Generate the HTML template with embedded data and Three.js code."""

    layer_data_json = json.dumps(layer_data)

    return f'''<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0a12;
            color: #eee;
            overflow: hidden;
        }}
        #canvas {{ width: 100vw; height: 100vh; display: block; }}
        .header {{
            position: fixed;
            top: 0; left: 0; right: 0;
            padding: 12px 20px;
            background: rgba(10, 10, 18, 0.92);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid #1a1a2e;
            display: flex;
            align-items: center;
            gap: 20px;
            z-index: 100;
            flex-wrap: wrap;
        }}
        h1 {{ font-size: 1.1em; font-weight: 500; color: #4ade80; }}
        .controls {{ display: flex; align-items: center; gap: 18px; flex-wrap: wrap; }}
        .control-group {{ display: flex; align-items: center; gap: 8px; }}
        label {{ font-size: 0.82em; color: #666; }}
        input[type="range"] {{ width: 140px; accent-color: #4ade80; cursor: pointer; }}
        #layerValue, #progressValue {{
            min-width: 35px;
            font-weight: 600;
            color: #4ade80;
            font-size: 0.9em;
            font-variant-numeric: tabular-nums;
        }}
        .toggle-btn {{
            padding: 5px 12px;
            border: 1px solid #1a1a2e;
            background: transparent;
            color: #666;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.15s;
            font-size: 0.82em;
        }}
        .toggle-btn:hover {{ border-color: #4ade80; color: #aaa; }}
        .toggle-btn.active {{ background: #4ade80; border-color: #4ade80; color: #000; }}
        .stats {{ font-size: 0.75em; color: #333; }}

        .color-legend {{
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 0.75em;
            color: #666;
            margin-left: 10px;
        }}
        .legend-bar {{
            width: 80px;
            height: 8px;
            border-radius: 4px;
            background: linear-gradient(to right, #3b82f6, #22c55e, #ef4444);
        }}

        .info-panel {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: rgba(10, 10, 18, 0.95);
            backdrop-filter: blur(12px);
            padding: 14px 16px;
            border-radius: 8px;
            border: 1px solid #1a1a2e;
            min-width: 260px;
            max-height: 80vh;
            overflow-y: auto;
            display: none;
            font-size: 0.82em;
        }}
        .info-panel h3 {{
            color: #4ade80;
            margin-bottom: 10px;
            font-size: 0.9em;
            font-weight: 500;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .info-panel .close-btn {{
            cursor: pointer;
            color: #666;
            font-size: 1.2em;
            line-height: 1;
        }}
        .info-panel .close-btn:hover {{ color: #fff; }}
        .info-section {{
            margin-bottom: 12px;
            padding-bottom: 10px;
            border-bottom: 1px solid #1a1a2e;
        }}
        .info-section:last-child {{ border-bottom: none; margin-bottom: 0; }}
        .info-section-title {{
            font-size: 0.75em;
            color: #4ade80;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 6px;
        }}
        .info-panel .row {{
            display: flex;
            justify-content: space-between;
            margin: 4px 0;
        }}
        .info-panel .label {{ color: #555; }}
        .info-panel .value {{ color: #ccc; font-variant-numeric: tabular-nums; }}
        .quality-badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 3px;
            font-weight: 600;
        }}

        .help {{
            position: fixed;
            bottom: 20px;
            left: 20px;
            font-size: 0.72em;
            color: #2a2a3e;
        }}

        .play-btn {{
            width: 28px;
            height: 28px;
            border: 1px solid #1a1a2e;
            background: transparent;
            color: #666;
            border-radius: 4px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.15s;
        }}
        .play-btn:hover {{ border-color: #4ade80; color: #4ade80; }}
        .play-btn.playing {{ background: #4ade80; border-color: #4ade80; color: #000; }}
    </style>
</head>
<body>
    <canvas id="canvas"></canvas>
    <div class="header">
        <h1>{title}</h1>
        <div class="controls">
            <div class="control-group">
                <label>Layer</label>
                <input type="range" id="layerSlider" min="0" max="{max_layer}" value="{max_layer}">
                <span id="layerValue">{max_layer}</span>
            </div>
            <div class="control-group">
                <button class="toggle-btn active" id="cumulativeBtn">Cumulative</button>
                <button class="toggle-btn" id="singleBtn">Single</button>
            </div>
            <div class="control-group">
                <label>Progress</label>
                <input type="range" id="progressSlider" min="0" max="100" value="100">
                <span id="progressValue">100%</span>
                <button class="play-btn" id="playBtn" title="Animate">&#9654;</button>
            </div>
            <div class="color-legend">
                <span>-1</span>
                <div class="legend-bar"></div>
                <span>+1</span>
            </div>
        </div>
        <span class="stats">{total_points:,} pts</span>
    </div>

    <div class="info-panel" id="infoPanel">
        <h3>
            Element Info
            <span class="close-btn" onclick="document.getElementById('infoPanel').style.display='none'">&times;</span>
        </h3>

        <div class="info-section">
            <div class="info-section-title">Identity</div>
            <div class="row"><span class="label">Index</span><span class="value" id="infoIdx">-</span></div>
            <div class="row"><span class="label">Layer</span><span class="value" id="infoLayer">-</span></div>
            <div class="row"><span class="label">Partition</span><span class="value" id="infoPartition">-</span></div>
            <div class="row"><span class="label">Event</span><span class="value" id="infoEvent">-</span></div>
        </div>

        <div class="info-section">
            <div class="info-section-title">Thermal</div>
            <div class="row"><span class="label">Quality</span><span class="value"><span id="infoQuality" class="quality-badge">-</span></span></div>
            <div class="row"><span class="label">Temperature</span><span class="value"><span id="infoTemp">-</span> K</span></div>
            <div class="row"><span class="label">Env Temp</span><span class="value"><span id="infoEnvTemp">-</span> K</span></div>
            <div class="row"><span class="label">Fan Speed</span><span class="value" id="infoFan">-</span></div>
        </div>

        <div class="info-section">
            <div class="info-section-title">Geometry</div>
            <div class="row"><span class="label">Height</span><span class="value"><span id="infoHeight">-</span> m</span></div>
            <div class="row"><span class="label">Width</span><span class="value"><span id="infoWidth">-</span> m</span></div>
        </div>

        <div class="info-section">
            <div class="info-section-title">Position</div>
            <div class="row"><span class="label">X</span><span class="value"><span id="infoPosX">-</span> m</span></div>
            <div class="row"><span class="label">Y</span><span class="value"><span id="infoPosY">-</span> m</span></div>
            <div class="row"><span class="label">Z</span><span class="value"><span id="infoPosZ">-</span> m</span></div>
            <div class="row"><span class="label">Time</span><span class="value"><span id="infoTime">-</span> s</span></div>
        </div>
    </div>

    <div class="help">Drag: rotate | Scroll: zoom | Shift+drag: pan | Click: inspect</div>

    <script type="importmap">
    {{ "imports": {{
        "three": "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js",
        "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"
    }}}}
    </script>
    <script type="module">
        import * as THREE from 'three';
        import {{ OrbitControls }} from 'three/addons/controls/OrbitControls.js';

        const layerData = {layer_data_json};
        const maxLayer = {max_layer};

        let currentMode = 'cumulative';
        let currentLayer = maxLayer;
        let currentProgress = 100;
        let isPlaying = false;
        let animationSpeed = 0.5;

        const canvas = document.getElementById('canvas');
        const renderer = new THREE.WebGLRenderer({{ canvas, antialias: true }});
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.setClearColor(0x0a0a12);

        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(50, window.innerWidth / window.innerHeight, 0.1, 1000);
        camera.position.set(40, 35, 40);

        const controls = new OrbitControls(camera, canvas);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;

        function qualityToColor(q) {{
            q = Math.max(-1, Math.min(1, q));
            let r, g, b;
            if (q < 0) {{
                const t = q + 1;
                r = 0.23 * (1 - t);
                g = 0.51 * (1 - t) + 0.77 * t;
                b = 0.96 * (1 - t) + 0.33 * t;
            }} else {{
                const t = q;
                r = 0.13 * (1 - t) + 0.94 * t;
                g = 0.77 * (1 - t) + 0.27 * t;
                b = 0.33 * (1 - t) + 0.27 * t;
            }}
            return new THREE.Color(r, g, b);
        }}

        function qualityToHex(q) {{
            const c = qualityToColor(q);
            return '#' + c.getHexString();
        }}

        const layerGroups = [];
        const layerPointCounts = [];

        layerData.forEach(ld => {{
            const group = new THREE.Group();
            group.userData.layer = ld.layer;
            group.userData.segments = [];

            let layerPts = 0;

            ld.segments.forEach(seg => {{
                if (seg.points.length < 2) return;

                const positions = [];
                const colors = [];

                seg.points.forEach((p, i) => {{
                    positions.push(p[0], p[1], p[2]);
                    const col = qualityToColor(seg.qualities[i]);
                    colors.push(col.r, col.g, col.b);
                }});

                const geometry = new THREE.BufferGeometry();
                geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
                geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));

                const material = new THREE.LineBasicMaterial({{ vertexColors: true, linewidth: 1 }});
                const line = new THREE.Line(geometry, material);
                line.userData.layer = ld.layer;
                line.userData.meta = seg.meta;
                line.userData.pointCount = seg.points.length;
                line.userData.fullPositions = positions.slice();
                line.userData.fullColors = colors.slice();

                group.add(line);
                group.userData.segments.push(line);
                layerPts += seg.points.length;
            }});

            scene.add(group);
            layerGroups.push(group);
            layerPointCounts.push(layerPts);
        }});

        const gridHelper = new THREE.GridHelper(100, 50, 0x151520, 0x0c0c14);
        gridHelper.position.y = -5;
        scene.add(gridHelper);

        function getVisiblePointCount() {{
            let total = 0;
            layerGroups.forEach((group, i) => {{
                const layer = group.userData.layer;
                const visible = currentMode === 'cumulative' ? layer <= currentLayer : layer === currentLayer;
                if (visible) total += layerPointCounts[i];
            }});
            return total;
        }}

        function updateVisibility() {{
            const totalVisible = getVisiblePointCount();
            const showPoints = Math.floor(totalVisible * currentProgress / 100);
            let pointsSoFar = 0;

            layerGroups.forEach(group => {{
                const layer = group.userData.layer;
                const shouldShow = currentMode === 'cumulative' ? layer <= currentLayer : layer === currentLayer;
                group.visible = shouldShow;

                if (!shouldShow) return;

                group.userData.segments.forEach(line => {{
                    const linePoints = line.userData.pointCount;
                    const lineStart = pointsSoFar;
                    const lineEnd = pointsSoFar + linePoints;

                    if (showPoints <= lineStart) {{
                        line.visible = false;
                    }} else if (showPoints >= lineEnd) {{
                        line.visible = true;
                        line.geometry.setDrawRange(0, linePoints);
                    }} else {{
                        line.visible = true;
                        const visibleCount = showPoints - lineStart;
                        line.geometry.setDrawRange(0, visibleCount);
                    }}

                    pointsSoFar += linePoints;
                }});
            }});
        }}

        const layerSlider = document.getElementById('layerSlider');
        const progressSlider = document.getElementById('progressSlider');
        const playBtn = document.getElementById('playBtn');

        layerSlider.addEventListener('input', e => {{
            currentLayer = parseInt(e.target.value);
            document.getElementById('layerValue').textContent = currentLayer;
            updateVisibility();
        }});

        progressSlider.addEventListener('input', e => {{
            currentProgress = parseInt(e.target.value);
            document.getElementById('progressValue').textContent = currentProgress + '%';
            updateVisibility();
        }});

        document.getElementById('cumulativeBtn').addEventListener('click', () => {{
            currentMode = 'cumulative';
            document.getElementById('cumulativeBtn').classList.add('active');
            document.getElementById('singleBtn').classList.remove('active');
            updateVisibility();
        }});

        document.getElementById('singleBtn').addEventListener('click', () => {{
            currentMode = 'single';
            document.getElementById('singleBtn').classList.add('active');
            document.getElementById('cumulativeBtn').classList.remove('active');
            updateVisibility();
        }});

        playBtn.addEventListener('click', () => {{
            isPlaying = !isPlaying;
            playBtn.classList.toggle('playing', isPlaying);
            playBtn.innerHTML = isPlaying ? '&#10074;&#10074;' : '&#9654;';
            if (isPlaying && currentProgress >= 100) {{
                currentProgress = 0;
                progressSlider.value = 0;
                document.getElementById('progressValue').textContent = '0%';
            }}
        }});

        const raycaster = new THREE.Raycaster();
        raycaster.params.Line.threshold = 0.5;
        const mouse = new THREE.Vector2();

        canvas.addEventListener('click', e => {{
            mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
            mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;

            raycaster.setFromCamera(mouse, camera);
            const intersects = raycaster.intersectObjects(scene.children, true);

            for (const hit of intersects) {{
                // Skip if no metadata or object/parent not visible
                if (!hit.object.userData.meta || !hit.object.visible) continue;
                if (hit.object.parent && !hit.object.parent.visible) continue;

                // Check if this element's layer matches current visibility settings
                const hitLayer = hit.object.userData.layer;
                const isLayerVisible = currentMode === 'cumulative'
                    ? hitLayer <= currentLayer
                    : hitLayer === currentLayer;
                if (!isLayerVisible) continue;

                const idx = Math.min(hit.index || 0, hit.object.userData.meta.length - 1);
                const m = hit.object.userData.meta[idx];

                document.getElementById('infoIdx').textContent = m.idx >= 0 ? m.idx : 'N/A';
                document.getElementById('infoLayer').textContent = m.layer;
                document.getElementById('infoPartition').textContent = m.partition;
                document.getElementById('infoEvent').textContent = m.event;

                const qBadge = document.getElementById('infoQuality');
                qBadge.textContent = m.quality.toFixed(6);
                qBadge.style.background = qualityToHex(m.quality);
                qBadge.style.color = Math.abs(m.quality) > 0.5 ? '#fff' : '#000';

                document.getElementById('infoTemp').textContent = m.temp.toFixed(2);
                document.getElementById('infoEnvTemp').textContent = m.env_temp.toFixed(2);
                document.getElementById('infoFan').textContent = m.fan_speed.toFixed(3);

                document.getElementById('infoHeight').textContent = m.height.toFixed(6);
                document.getElementById('infoWidth').textContent = m.width.toFixed(6);

                document.getElementById('infoPosX').textContent = m.x.toFixed(6);
                document.getElementById('infoPosY').textContent = m.y.toFixed(6);
                document.getElementById('infoPosZ').textContent = m.z.toFixed(6);
                document.getElementById('infoTime').textContent = m.t.toFixed(4);

                document.getElementById('infoPanel').style.display = 'block';
                break;
            }}
        }});

        window.addEventListener('resize', () => {{
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        }});

        let lastTime = 0;
        function animate(time) {{
            requestAnimationFrame(animate);

            if (isPlaying) {{
                const delta = time - lastTime;
                if (delta > 16) {{
                    currentProgress += animationSpeed;
                    if (currentProgress >= 100) {{
                        currentProgress = 100;
                        isPlaying = false;
                        playBtn.classList.remove('playing');
                        playBtn.innerHTML = '&#9654;';
                    }}
                    progressSlider.value = currentProgress;
                    document.getElementById('progressValue').textContent = Math.round(currentProgress) + '%';
                    updateVisibility();
                    lastTime = time;
                }}
            }} else {{
                lastTime = time;
            }}

            controls.update();
            renderer.render(scene, camera);
        }}
        animate(0);

        updateVisibility();
    </script>
</body>
</html>'''
