import os
from workflows import create_order_graph

# ワークフローの画像を生成するための処理
graph = create_order_graph()
png_graph = graph.get_graph().draw_mermaid_png()
with open("my_graph.png", "wb") as f:
    f.write(png_graph)

print(f"Graph saved as 'my_graph.png' in {os.getcwd()}")
