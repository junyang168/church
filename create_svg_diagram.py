import svgwrite
from svgwrite import px
from svgwrite.text import Text

def create_decision_tree_svg_with_arrows(output_path="decision_tree_diagram_arrows.svg"):
    """
    Creates an SVG file with a decision tree diagram, styled for a white background
    and using arrow lines.
    """
    # Define canvas dimensions
    width = 1200  # pixels
    height = 900  # pixels

    dwg = svgwrite.Drawing(output_path, profile='full', size=(f"{width}px", f"{height}px"))

    # Define colors for white background
    text_color = "#333333"  # Dark Gray
    line_color = "#666666"  # Medium Gray

    # Define common text style
    font_size = 40  # pixels
    font_family = "SimHei, sans-serif" # SimHei for Chinese, fallback to sans-serif

    # --- Define Arrowhead Marker ---
    # A marker is defined in the <defs> section and then referenced by lines.
    # It allows you to draw shapes (like arrows) at the start/end of paths/lines.
    arrow_marker_id = "TriangleArrow"
    marker_width = 10
    marker_height = 8

    marker = dwg.marker(id=arrow_marker_id,
                        viewBox=f"0 0 {marker_width} {marker_height}", # Viewbox of the marker itself
                        refX=marker_width, # The x-coordinate in the marker's coordinate system that will be placed at the line's endpoint
                        refY=marker_height / 2, # The y-coordinate in the marker's coordinate system that will be placed at the line's endpoint
                        markerUnits="strokeWidth", # Scale marker with stroke-width
                        markerWidth=marker_width,
                        markerHeight=marker_height,
                        orient="auto") # Automatically orient the arrow along the path

    # Add the path for the arrowhead (a simple triangle)
    marker.add(dwg.polygon([(0, 0), (marker_width, marker_height / 2), (0, marker_height)],
                           fill=line_color))
    dwg.defs.add(marker)

    # --- Add Text Elements ---

    # 1. Top Box: "可以吃，但勿叫人跌倒"
    text1_x = width / 2
    text1_y = 70
    dwg.add(Text("可以吃，但勿叫人跌倒",
                 insert=(text1_x, text1_y),
                 font_size=font_size,
                 font_family=font_family,
                 fill=text_color,
                 text_anchor="middle"))

    # 2. Left Branch - Condition: "95%叫人跌倒"
    text2_x = width * 0.25
    text2_y = 350
    dwg.add(Text("95%叫人跌倒",
                 insert=(text2_x, text2_y),
                 font_size=font_size,
                 font_family=font_family,
                 fill=text_color,
                 text_anchor="middle"))

    # 3. Left Branch - Outcome: "不可以吃"
    text3_x = width * 0.25
    text3_y = 550
    dwg.add(Text("不可以吃",
                 insert=(text3_x, text3_y),
                 font_size=font_size,
                 font_family=font_family,
                 fill=text_color,
                 text_anchor="middle"))

    # 4. Right Branch - Condition: "可能叫人跌倒"
    text4_x = width * 0.75
    text4_y = 350
    dwg.add(Text("可能叫人跌倒",
                 insert=(text4_x, text4_y),
                 font_size=font_size,
                 font_family=font_family,
                 fill=text_color,
                 text_anchor="middle"))

    # 5. Right Branch - Sub-condition/Outcome 1: "叫人跌倒就不可吃"
    text5_x = width * 0.75
    text5_y = 550
    dwg.add(Text("叫人跌倒就不可吃",
                 insert=(text5_x, text5_y),
                 font_size=font_size,
                 font_family=font_family,
                 fill=text_color,
                 text_anchor="middle"))

    # 6. Right Branch - Sub-condition 2: "可能不叫人跌倒"
    text6_x = width * 0.75
    text6_y = 700
    dwg.add(Text("可能不叫人跌倒",
                 insert=(text6_x, text6_y),
                 font_size=font_size,
                 font_family=font_family,
                 fill=text_color,
                 text_anchor="middle"))

    # 7. Right Branch - Sub-outcome 2: "不叫人跌倒就可吃"
    text7_x = width * 0.75
    text7_y = 850
    dwg.add(Text("不叫人跌倒就可吃",
                 insert=(text7_x, text7_y),
                 font_size=font_size,
                 font_family=font_family,
                 fill=text_color,
                 text_anchor="middle"))

    # --- Add Lines/Connectors with Arrowheads ---
    line_stroke_width = 3

    # Helper function to add a line with an arrowhead
    def add_arrow_line(x1, y1, x2, y2):
        line = dwg.line(start=(x1, y1), end=(x2, y2),
                        stroke=line_color, stroke_width=line_stroke_width)
        line['marker-end'] = f"url(#{arrow_marker_id})" # Apply the defined marker
        dwg.add(line)

    # Line 1: From Top Box to Left Branch (95%)
    add_arrow_line(text1_x, text1_y + font_size / 2 + 10, text2_x, text2_y - font_size / 2 - 10)

    # Line 2: From Top Box to Right Branch (Possibly)
    add_arrow_line(text1_x, text1_y + font_size / 2 + 10, text4_x, text4_y - font_size / 2 - 10)

    # Line 3: From Left Branch (95%) to Left Outcome (Cannot eat)
    add_arrow_line(text2_x, text2_y + font_size / 2 + 10, text3_x, text3_y - font_size / 2 - 10)

    # Line 4: From Right Branch (Possibly) to Sub-outcome 1 (If it causes, cannot eat)
    add_arrow_line(text4_x, text4_y + font_size / 2 + 10, text5_x, text5_y - font_size / 2 - 10)

    # Line 5: From Right Branch (Possibly) to Sub-condition 2 (Possibly does not cause)
    add_arrow_line(text4_x, text4_y + font_size / 2 + 10, text6_x, text6_y - font_size / 2 - 10)

    # Line 6: From Sub-condition 2 (Possibly does not cause) to Sub-outcome 2 (If it does not cause, can eat)
    add_arrow_line(text6_x, text6_y + font_size / 2 + 10, text7_x, text7_y - font_size / 2 - 10)


    dwg.save()
    print(f"SVG diagram saved to {output_path}")

# Run the script
create_decision_tree_svg_with_arrows()