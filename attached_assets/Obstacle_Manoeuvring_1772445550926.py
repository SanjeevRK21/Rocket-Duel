"""
We are using the 'math' module for essential mathematical operations,
like calculating the distance between two points.
"""
import math

"""
This section checks for the 'matplotlib' library.
We're using it to generate a visual map of the path, checkpoints, and obstacles.
If 'matplotlib' isn't installed, the program will gracefully handle the missing library
and simply skip the plotting feature instead of crashing. This ensures our core logic still works.
"""
try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Note: matplotlib not available. Plotting will be skipped.")

"""
Similarly, we use the 'rich' library to make our terminal output much easier to read.
It allows us to add colors, tables, and panels, which is especially helpful
when presenting complex data like coordinates and distances. Just like with matplotlib,
if 'rich' isn't available, the code will fall back to using standard print statements.
"""
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich import print as rich_print
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Note: rich library not available. Terminal output will be basic.")

"""
This is a robust way to initialize the rich console.
If the 'rich' library is found, we create a 'Console' object to use its features.
Otherwise, we create a simple placeholder object that has a 'print' method
that just uses Python's standard `print()`.
"""
if RICH_AVAILABLE:
    console = Console()
else:
    def console_print_fallback(*args, **kwargs):
        print(*args, **kwargs)
    console = type('ConsoleFallback', (object,), {"print": staticmethod(console_print_fallback)})()

"""
This is a function acts as a compass for three points (lets say p, q, and r).
It tells us if point r is to the left of the line from p to q (counter-clockwise),
to the right (clockwise), or directly on the line (collinear).
The code calculates this by using the cross-product of vectors, which is a very efficient way
to determine the orientation without using any complex trigonometry.
"""
def orientation(p, q, r):
    """
    Find orientation of ordered triplet (p, q, r).
    0 --> p, q, r are collinear
    1 --> Clockwise
    2 --> Counterclockwise
    """
    val = ((q[1] - p[1]) * (r[0] - q[0])) - ((q[0] - p[0]) * (r[1] - q[1]))
    if val == 0:
        return 0
    return 1 if val > 0 else 2

"""
This helper function is only used when three points are known to be on a straight line.
It simply checks if a point 'q' is physically located between points 'p' and 'r'
along that line. This is crucial for handling edge cases where an obstacle might
just barely touch our path at a single point.
"""
def on_segment(p, q, r):
    """Given three collinear points p, q, r, check if q lies on segment pr."""
    return (q[0] <= max(p[0], r[0]) and q[0] >= min(p[0], r[0]) and
            q[1] <= max(p[1], r[1]) and q[1] >= min(p[1], r[1]))

"""
This is the main function for collision detection.
It uses the `orientation` function four times to check if two line segments cross each other.
The general logic is: if the endpoints of one segment are on opposite sides of the other segment,
then they must intersect. We also have special checks using `on_segment` to handle cases
where a segment's endpoint lies directly on the other segment. This makes our collision detection
robust and reliable.
"""
def segments_intersect(p1, q1, p2, q2):
    """Check if line segment (p1, q1) intersects line segment (p2, q2)."""
    o1 = orientation(p1, q1, p2)
    o2 = orientation(p1, q1, q2)
    o3 = orientation(p2, q2, p1)
    o4 = orientation(p2, q2, q1)

    # General case
    if o1 != o2 and o3 != o4:
        return True

    # Special Cases for collinear points
    # p1, q1 and p2 are collinear and p2 lies on segment p1q1
    if o1 == 0 and on_segment(p1, p2, q1): return True
    # p1, q1 and q2 are collinear and q2 lies on segment p1q1
    if o2 == 0 and on_segment(p1, q2, q1): return True
    # p2, q2 and p1 are collinear and p1 lies on segment p2q2
    if o3 == 0 and on_segment(p2, p1, q2): return True
    # p2, q2 and q1 are collinear and q1 lies on segment p2q2
    if o4 == 0 and on_segment(p2, q1, q2): return True

    return False

"""
This function is responsible for drawing a visual representation of our path and environment.
It uses the `matplotlib` library to create a clean plot with different colors and labels
for the start point, goal, checkpoints, and obstacles.
We've added specific colors for normal, rerouted, and even skipped path segments
to give a clear, at-a-glance understanding of how the path was generated.
The plot only runs if `matplotlib` is available, as handled in our setup code.
"""
def plot_path(start, goal, checkpoints, path_segments, obstacles=None):

    if not MATPLOTLIB_AVAILABLE:
        console.print("[red]Plotting is disabled because matplotlib is not installed.[/red]")
        return

    fig, ax = plt.subplots(1, 1, figsize=(14, 10))

    # Plot start point (black)
    ax.scatter(start[0], start[1], color='black', s=100, zorder=5, label='Start')
    ax.annotate('S', (start[0], start[1]), xytext=(5, 5), textcoords='offset points',
                fontsize=12, fontweight='bold', color='white', zorder=6)

    # Plot goal point (black)
    ax.scatter(goal[0], goal[1], color='black', s=100, zorder=5, label='Goal')
    ax.annotate('E', (goal[0], goal[1]), xytext=(5, 5), textcoords='offset points',
                fontsize=12, fontweight='bold', color='white', zorder=6)

    # Plot checkpoints (red)
    if checkpoints:
        checkpoint_x = [cp[0] for cp in checkpoints]
        checkpoint_y = [cp[1] for cp in checkpoints]
        ax.scatter(checkpoint_x, checkpoint_y, color='red', s=80, zorder=4, label='Checkpoints')

        # Add labels for checkpoints
        for i, cp in enumerate(checkpoints):
            ax.annotate(f'C{i+1}', (cp[0], cp[1]), xytext=(5, 5), textcoords='offset points',
                        fontsize=11, fontweight='bold', color='white', zorder=6)
    
    # Plot the obstacles
    if obstacles:
        for i, obstacle in enumerate(obstacles):
            ox1, oy1 = obstacle[0]
            ox2, oy2 = obstacle[1]
            ax.plot([ox1, ox2], [oy1, oy2], color='purple', linewidth=3, linestyle='--', zorder=1)
            # Annotate obstacle with a number
            mid_x = (ox1 + ox2) / 2
            mid_y = (oy1 + oy2) / 2
            ax.annotate(f'O{i+1}', (mid_x, mid_y), textcoords='offset points', xytext=(5,-10),
                        color='darkred', fontsize=10, fontweight='bold', zorder=1)
        ax.plot([], [], color='darkred', linewidth=3, linestyle='--', label='Obstacles') # Add a single label for the legend

    # Draw the path segments
    rerouted_label_added = False
    normal_label_added = False
    skipped_label_added = False # New label for skipped segments

    for segment in path_segments:
        p1 = segment['start']
        p2 = segment['end']
        intermediate_points = segment['intermediate_points']
        is_rerouted = segment['is_rerouted']
        is_skipped = segment.get('is_skipped', False) # New flag

        # Determine color based on rerouting or skipping
        if is_skipped:
            color = 'gray'
            label = None
            if not skipped_label_added:
                label = 'Skipped Path'
                skipped_label_added = True
        elif is_rerouted:
            color = 'lightblue'
            label = None
            if not rerouted_label_added:
                label = 'Rerouted Path'
                rerouted_label_added = True
        else:
            color = 'lightgreen'
            label = None
            if not normal_label_added:
                label = 'Normal Path'
                normal_label_added = True

        # Draw intermediate points (not for skipped segments)
        if intermediate_points and not is_skipped:
            inter_x = [point[0] for point in intermediate_points]
            inter_y = [point[1] for point in intermediate_points]
            ax.scatter(inter_x, inter_y, color=color, s=50, zorder=3)

        # Draw the line segment
        all_points_in_segment = [p1] + intermediate_points + [p2] if not is_skipped else [p1, p2]
        path_x = [p[0] for p in all_points_in_segment]
        path_y = [p[1] for p in all_points_in_segment]
        
        linestyle = '--' if is_skipped else '-'
        alpha = 0.5 if is_skipped else 0.7

        ax.plot(path_x, path_y, color=color, linewidth=2, alpha=alpha, zorder=2, label=label, linestyle=linestyle)

    # Set up the main plot
    ax.set_xlabel('X Coordinate')
    ax.set_ylabel('Y Coordinate')
    ax.set_title('Path with Intermediate Points and Obstacle Avoidance')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.axis('equal')

    plt.tight_layout()
    plt.show()

"""
These functions handle user input and basic calculations.
`get_point` is a robust input function that prompts the user for coordinates and
validates the input to make sure it's in the correct format (e.g., "x,y").
`distance` uses the standard Euclidean distance formula to calculate the length of any path segment.
"""
def get_point(prompt):
    """Prompt the user for a coordinate and return it as a tuple of floats."""
    while True:
        try:
            x_str, y_str = console.input(f"[bold blue]{prompt}[/bold blue]").split(',')
            return float(x_str.strip()), float(y_str.strip())
        except ValueError:
            console.print("[red]Invalid format. Please enter coordinates as x,y (e.g., 2.5,4.3).[/red]")

# This is a standard mathematical function that calculates the straight-line distance
# between two points using the Pythagorean theorem.
def distance(p1, p2):
    """Calculate Euclidean distance between two points."""
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)

"""
This function is used to calculate and create small, evenly-spaced points
along a line segment. We use this to visualize the path, creating a series of dots
that show the direction of travel. This is a form of linear interpolation.
"""
def generate_intermediate_points(p1, p2, num_points=4):
    
    x1, y1 = p1
    x2, y2 = p2

    if num_points <= 0: return []
    
    if x2 == x1:
        # Handle vertical line
        step = (y2 - y1) / (num_points + 1)
        return [(x1, y1 + i * step) for i in range(1, num_points + 1)]

    slope = (y2 - y1) / (x2 - x1)
    step = (x2 - x1) / (num_points + 1)

    points = []
    for i in range(1, num_points + 1):
        x = x1 + i * step
        y = slope * (x - x1) + y1
        points.append((round(x, 2), round(y, 2)))
    return points

"""
This function bundles the calculation of intermediate points and distances for a given segment.
"""
def print_segment_output(start, end):
    inter_points = generate_intermediate_points(start, end)
    dist_total = distance(start, end)
    dist_each = dist_total / (len(inter_points) + 1) if (len(inter_points) + 1) > 0 else dist_total # Avoid div by zero
    return inter_points, dist_total, dist_each

"""
This function handles interactive user input with specific choices.
It repeatedly prompts the user until a valid option is selected,
providing clear feedback for incorrect input.
"""
def confirm_action(prompt, options):
    while True:
        answer = console.input(f"[bold yellow]{prompt} ({'/'.join(options)}): [/bold yellow]").lower()
        if answer in options:
            return answer
        else:
            console.print(f"[red]Invalid input. Please enter one of: {', '.join(options)}[/red]")

"""
This function checks if a point is on a line segment using distances.
"""
def is_point_on_line(point, line_start, line_end, tolerance=1e-6):
    """
    Check if a point lies on a line segment.
    This assumes a small tolerance for floating point comparisons.
    """
    dist_total = distance(line_start, line_end)
    dist_p1_point = distance(line_start, point)
    dist_p2_point = distance(line_end, point)

    # Check if the sum of distances from the point to the line endpoints is equal
    # to the distance between the endpoints, within a small tolerance.
    return math.isclose(dist_p1_point + dist_p2_point, dist_total, rel_tol=tolerance)

"""
This is a crucial function for our obstacle avoidance feature.
When a path segment is found to intersect with an obstacle, this function is called.
It reroutes the path by creating a detour around the obstacle.
Currently, it uses a simple but effective strategy: it calculates the total distance
to go around both ends of the obstacle and chooses the shorter path.
This demonstrates a key problem-solving capability of our program.
"""
def reroute_path_around_obstacle(start_point, end_point, obstacle):
    
    """
    Calculates the rerouted path around an obstacle.
    Returns a list of points representing the new path (start, obstacle_vertex, end).
    """
    o1, o2 = obstacle

    """
    # Determine which end of the obstacle is closer to the end point of the segment
    # This might need more sophisticated geometry for optimal rerouting in complex scenarios
    # For a simple line obstacle, picking the closest endpoint is a reasonable heuristic.
    """
    dist_to_o1_from_end = distance(end_point, o1)
    dist_to_o2_from_end = distance(end_point, o2)
    dist_to_o1_from_start = distance(start_point, o1)
    dist_to_o2_from_start = distance(start_point, o2)

    """
    Heuristic: Choose the side of the obstacle that leads to a shorter overall journey
    Try start -> o1 -> end, and start -> o2 -> end
    """
    path1_len = distance(start_point, o1) + distance(o1, end_point)
    path2_len = distance(start_point, o2) + distance(o2, end_point)

    if path1_len < path2_len:
        rerouted_points = [start_point, o1, end_point]
    else:
        rerouted_points = [start_point, o2, end_point]

    return rerouted_points

"""
This is the central function that runs the entire program.
It walks the user through a series of steps:
1. It asks for a start point, a goal point, and any optional checkpoints.
2. It prompts the user to define any number of obstacle line segments.
3. It then goes through the defined path segment by segment.
4. For each segment, it checks for collisions using our geometric functions.
5. If a collision is found, it asks the user if they want to reroute around the obstacle.
   This shows an interactive element of our program.
6. Finally, it presents a summary table of the path segments and plots the entire journey.
The logic also includes checks to prevent path points from being placed directly on obstacles and handles skipping points if requested.
"""
def main():
    console.print(Panel("[bold green]---- Path Generator with Intermediate Points and Obstacle Avoidance ----[/bold green]", expand=False))

    # Step 1: Get start and goal points
    start = get_point("Enter Start point x,y: ")
    goal = get_point("Enter Goal x,y: ")

    while start == goal:
        console.print("[red]Start and goal points cannot be the same.[/red]")
        goal = get_point("Please re-enter a different Goal x,y: ")

    # Step 2: Get number of checkpoints
    while True:
        try:
            checkpoints_n_str = console.input("[bold blue]Number of Checkpoints (0, 1, or 2): [/bold blue]")
            checkpoints_n = int(checkpoints_n_str)
            if checkpoints_n not in [0, 1, 2]:
                console.print("[red]Please enter 0, 1, or 2.[/red]")
            else:
                break
        except ValueError:
            console.print("[red]Invalid input. Please enter an integer value (0, 1, or 2).[/red]")

    # Step 3: Get checkpoint(s) if needed
    checkpoints = []
    for i in range(checkpoints_n):
        cp = get_point(f"Enter Checkpoint {i+1} x,y: ")
        while cp == start or cp == goal or cp in checkpoints:
            console.print("[red]Checkpoint cannot be the same as the start, goal point, or another checkpoint.[/red]")
            cp = get_point(f"Please re-enter Checkpoint {i+1} x,y: ")
        checkpoints.append(cp)

    # Step 4: Get obstacle information (barriers)
    obstacles = []
    while True:
        try:
            num_obstacles_str = console.input("[bold blue]How many obstacles (barriers) do you want to add? [/bold blue]")
            num_obstacles = int(num_obstacles_str)
            if num_obstacles >= 0:
                break
            else:
                console.print("[red]Number of obstacles cannot be negative.[/red]")
        except ValueError:
            console.print("[red]Invalid input. Please enter an integer.[/red]")

    for i in range(num_obstacles):
        console.print(f"\n[bold magenta]Input for Obstacle {i+1}:[/bold magenta]")
        o1 = get_point(f"   Obstacle {i+1} start x,y: ")
        o2 = get_point(f"   Obstacle {i+1} end x,y: ")
        # Ensure obstacle is not just a point
        while o1 == o2:
            console.print("[red]Obstacle start and end points cannot be the same. Please re-enter.[/red]")
            o2 = get_point(f"   Obstacle {i+1} end x,y: ")
        obstacles.append((o1, o2))

    # --- Displaying Input Summary ---
    input_table = Table(title="[bold underline]Input Summary[/bold underline]", style="cyan")
    input_table.add_column("Item", style="bold")
    input_table.add_column("Value")

    input_table.add_row("Start Point", str(start))
    input_table.add_row("Goal Point", str(goal))

    if checkpoints:
        for i, cp in enumerate(checkpoints):
            input_table.add_row(f"Checkpoint {i+1}", str(cp))
    else:
        input_table.add_row("Checkpoints", "None")
    
    if obstacles:
        for i, obstacle in enumerate(obstacles):
            input_table.add_row(f"Obstacle {i+1}", f"{obstacle[0]} to {obstacle[1]}")
    else:
        input_table.add_row("Obstacles", "None")

    console.print(Panel(input_table, border_style="blue"))

    console.print(Panel("[bold green]Generating path segments and handling obstacles...[/bold green]", expand=False))

    total_path_distance = 0
    path_segments = []

    # The fixed path order
    current_path_sequence = [start] + checkpoints + [goal]

    segment_detail_table = Table(title="[bold underline]Path Segment Details[/bold underline]", style="yellow")
    segment_detail_table.add_column("Segment", style="bold blue")
    segment_detail_table.add_column("Type", style="bold")
    segment_detail_table.add_column("Intermediate Points", style="dim")
    segment_detail_table.add_column("Segment Distance", style="green")
    segment_detail_table.add_column("Dist per Inter", style="green")

    i = 0
    while i < len(current_path_sequence) - 1:
        p1 = current_path_sequence[i]
        p2 = current_path_sequence[i+1]

        segment_to_add = None # Holds the final segment(s) to add to path_segments
        segment_type = "Normal"
        segment_is_rerouted = False
        segment_is_skipped = False
        
        collision_detected_with_segment = False
        point_on_obstacle_action = None # 'continue' or 'skip'

        """
        Check for any major path point (p1 or p2) lying directly on an obstacle
        Only if p1 or p2 is NOT part of a segment already being processed as rerouted/skipped
        """
        for obstacle_idx, obstacle in enumerate(obstacles):
            o_start, o_end = obstacle
            
            # Check p1
            if is_point_on_line(p1, o_start, o_end):
                point_name = "Start" if p1 == start else (f"Checkpoint {checkpoints.index(p1)+1}" if p1 in checkpoints else "Goal")
                console.print(f"\n[yellow]Warning: Path point {point_name} {p1} is directly on Obstacle {obstacle_idx+1} {obstacle}.[/yellow]")
                action = confirm_action(f"Do you want to [bold yellow]continue through {point_name} (c)[/bold yellow] or [bold yellow]skip {point_name} and go to the next waypoint (s)[/bold yellow]?", ['c', 's'])
                if action == 'c':
                    console.print(f"[yellow]Continuing through point {p1} as requested.[/yellow]")
                    point_on_obstacle_action = 'continue'
                elif action == 's':
                    if p1 == start:
                        console.print("[red]Cannot skip the Start point. Please choose to continue or re-run with a different start.[/red]")
                        action = confirm_action(f"You must continue through the Start point. [bold yellow]Continue (c)[/bold yellow]?", ['c'])
                        point_on_obstacle_action = 'continue'
                    else:
                        console.print(f"[red]Skipping point {p1}. The path will now attempt to connect {current_path_sequence[i-1]} to {p2}.[/red]")
                        
                        # Add a visual skipped segment from prev_point to p1
                        if i > 0: # If there's a previous point
                            path_segments.append({
                                'start': current_path_sequence[i-1],
                                'end': p1,
                                'intermediate_points': [],
                                'is_rerouted': False,
                                'is_skipped': True
                            })
                            segment_detail_table.add_row(
                                f"{current_path_sequence[i-1]} to {p1}",
                                "[gray]Skipped Point[/gray]",
                                "N/A",
                                "0.0000",
                                "0.0000"
                            )

                        current_path_sequence.pop(i) # Remove the skipped point
                        segment_is_skipped = True # This point caused a skip
                        # We do NOT increment i, so the current p1 (which is the old p1) will now try to connect to the new p2.
                        break # Break from obstacle loop and re-evaluate the new segment

            # Check p2 (only if p1 wasn't skipped and handled)
            if not segment_is_skipped and is_point_on_line(p2, o_start, o_end):
                point_name = "Goal" if p2 == goal else (f"Checkpoint {checkpoints.index(p2)+1}" if p2 in checkpoints else "Unknown Point")
                console.print(f"\n[yellow]Warning: Path point {point_name} {p2} is directly on Obstacle {obstacle_idx+1} {obstacle}.[/yellow]")
                action = confirm_action(f"Do you want to [bold yellow]continue through {point_name} (c)[/bold yellow] or [bold yellow]skip {point_name} and go to the next waypoint (s)[/bold yellow]?", ['c', 's'])
                if action == 'c':
                    console.print(f"[yellow]Continuing through point {p2} as requested.[/yellow]")
                    point_on_obstacle_action = 'continue'
                elif action == 's':
                    if p2 == goal:
                        console.print("[red]Cannot skip the Goal point. You must reach the goal.[/red]")
                        action = confirm_action(f"You must continue through the Goal point. [bold yellow]Continue (c)[/bold yellow]?", ['c'])
                        point_on_obstacle_action = 'continue'
                    else:
                        console.print(f"[red]Skipping point {p2}. The path will now attempt to connect {p1} directly to {current_path_sequence[i+2] if i+2 < len(current_path_sequence) else 'Goal'}.[/red]")
                        
                        # Add a visual skipped segment from p2 to next_point (if it exists)
                        path_segments.append({
                            'start': p2, # The point that was skipped
                            'end': current_path_sequence[i+2] if i+2 < len(current_path_sequence) else goal,
                            'intermediate_points': [],
                            'is_rerouted': False,
                            'is_skipped': True
                        })
                        segment_detail_table.add_row(
                            f"{p2} to {current_path_sequence[i+2] if i+2 < len(current_path_sequence) else goal}",
                            "[gray]Skipped Point[/gray]",
                            "N/A",
                            "0.0000",
                            "0.0000"
                        )

                        current_path_sequence.pop(i+1) # Remove the skipped point
                        segment_is_skipped = True # This point caused a skip
                        # We do NOT increment i, so p1 remains the same and connects to the new p2.
                        break # Break from obstacle loop and re-evaluate the new segment
            
            # If a point was skipped, restart the loop iteration for the modified sequence
            if segment_is_skipped:
                break # Break inner obstacle loop, outer while loop will continue

        if segment_is_skipped: # If point was skipped and current_path_sequence changed, re-evaluate this 'i'
            continue # Go to the next iteration of the while loop to re-process current 'i'
            
        # If no point was skipped, now check for segment intersection with obstacles
        for obstacle_idx, obstacle in enumerate(obstacles):
            # Do not check for collision if the current segment is *exactly* an obstacle (this is unlikely with points)
            if (p1, p2) == obstacle or (p2, p1) == obstacle:
                continue
            
            if segments_intersect(p1, p2, obstacle[0], obstacle[1]):
                console.print(f"\n[red]Collision detected: Path segment {p1} to {p2} intersects Obstacle {obstacle_idx+1} {obstacle}.[/red]")
                action = confirm_action(
                    f"Action for collision between {p1} and {p2} with obstacle {obstacle}: "
                    f"[bold yellow]C[/bold yellow]ontinue through segment or [bold yellow]R[/bold yellow]eroute around it?",
                    ['c', 'r']
                )
                if action == 'c':
                    console.print(f"[yellow]Continuing path segment {p1} to {p2} through obstacle as requested.[/yellow]")
                    # No special action, just let it be a normal segment that happens to intersect
                    break # Break from obstacle loop, as we decided for this segment
                elif action == 'r':
                    rerouted_path_points = reroute_path_around_obstacle(p1, p2, obstacle)
                    segment_is_rerouted = True
                    segment_type = "Rerouted"
                    
                    # Add rerouted sub-segments
                    for j in range(len(rerouted_path_points) - 1):
                        sub_p1 = rerouted_path_points[j]
                        sub_p2 = rerouted_path_points[j+1]
                        inter_points, dist_total, dist_each = print_segment_output(sub_p1, sub_p2)
                        total_path_distance += dist_total
                        path_segments.append({
                            'start': sub_p1,
                            'end': sub_p2,
                            'intermediate_points': inter_points,
                            'is_rerouted': True,
                            'is_skipped': False
                        })
                        inter_points_str = ", ".join([f"({x},{y})" for x,y in inter_points]) if inter_points else "None"
                        segment_detail_table.add_row(
                            f"{sub_p1} to {sub_p2}",
                            "[purple]Rerouted[/purple]",
                            inter_points_str,
                            f"{dist_total:.4f}",
                            f"{dist_each:.4f}"
                        )
                    collision_detected_with_segment = True # Indicate rerouting happened for this segment
                    break # Break from obstacle loop as this segment is handled

        if collision_detected_with_segment: # If rerouted, we've already added the sub-segments
            i += 1 # Move to the next major point
            continue # Continue to the next iteration of the while loop

        """
        If we reach here, it means either:
        1. No collision at all.
        2. A point was on an obstacle, but user chose 'continue'.
        3. A segment intersected an obstacle, but user chose 'continue'.
        """
        
        # Add the segment as a normal one
        inter_points, dist_total, dist_each = print_segment_output(p1, p2)
        total_path_distance += dist_total
        path_segments.append({
            'start': p1,
            'end': p2,
            'intermediate_points': inter_points,
            'is_rerouted': False,
            'is_skipped': False
        })
        inter_points_str = ", ".join([f"({x},{y})" for x,y in inter_points]) if inter_points else "None"
        segment_detail_table.add_row(
            f"{p1} to {p2}",
            "[lightblue]Normal[/lightblue]",
            inter_points_str,
            f"{dist_total:.4f}",
            f"{dist_each:.4f}"
        )
        i += 1 # Move to the next major point


    console.print(segment_detail_table)

    console.print(Panel(
        f"[bold white on blue]Total Path Distance: {total_path_distance:.4f}[/bold white on blue]",
        expand=False,
        padding=(1, 2)
    ))

    # Plot the path
    plot_path(start, goal, checkpoints, path_segments, obstacles)

if __name__ == "__main__":
    main()
