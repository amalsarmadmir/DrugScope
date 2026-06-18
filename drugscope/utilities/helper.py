def print_reactions_chart(data: list[tuple[str, int]], max_bar_length: int = 20) -> None:
    if not data:
        return

    # 1. Find the maximum value to calculate the scale factor
    max_val = max(count for _, count in data)
    
    # 2. Find the longest label length so we can dynamically align the text
    max_label_len = max(len(label) for label, _ in data)

    print("=== [Top 5 Patient Reactions] ===")
    
    for i, (label, count) in enumerate(data, 1):
        # Calculate how many blocks to print based on the scale factor
        bar_length = int((count / max_val) * max_bar_length) if max_val > 0 else 0
        bar = "█" * bar_length
        
        # Format string: 
        # i: index
        # label: left-aligned with padding equal to the longest label
        # bar: the generated block string
        # count: the raw number at the end
        print(f"{i}. {label:<{max_label_len}}: {bar} {count}")


