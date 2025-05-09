import tkinter as tk
from tkinter import filedialog, colorchooser, messagebox
from PIL import Image, ImageTk

# Global variables for application and image states
selected_color = None
new_rgb = None
original_pil = None
modified_pil = None
unique_colors = []
undo_stack = []
original_img = None
modified_img = None
selected_from_latest = False
threshold = None
preserve_bw = None
original_canvas = None
modified_canvas = None
original_color_frame = None
latest_color_frame = None
status_label = None


def load_image(path):
    global original_img, modified_img, original_pil, modified_pil
    global original_canvas, modified_canvas

    original_pil = Image.open(path).convert("RGBA")
    modified_pil = original_pil.copy()

    display_size = (250, 250)
    original_img = ImageTk.PhotoImage(original_pil.resize(display_size, Image.LANCZOS))
    modified_img = ImageTk.PhotoImage(modified_pil.resize(display_size, Image.LANCZOS))
    original_canvas.config(image=original_img)
    modified_canvas.config(image=modified_img)
    extract_and_show_colors(original_pil)


def upload_image():
    file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.bmp")])
    if file_path:
        load_image(file_path)


def extract_and_show_colors(pil_img):
    global unique_colors, original_color_frame, latest_color_frame
    
    # Clear previous color swatches
    for widget in original_color_frame.winfo_children():
        widget.destroy()
    for widget in latest_color_frame.winfo_children():
        widget.destroy()
        
    # Extract colors
    colors = pil_img.getcolors(maxcolors=16)
    if colors:
        colors.sort(reverse=True)
        unique_colors = [color for count, color in colors if len(color) >= 3][:10]
        
        # Display original colors
        for idx, color in enumerate(unique_colors):
            r, g, b, *_ = color
            color_frame = tk.Frame(original_color_frame, width=30, height=30, bg=f'#{r:02x}{g:02x}{b:02x}', 
                                  relief="raised", bd=1)
            color_frame.color_value = color
            color_frame.pack(side="left", padx=5)
            color_frame.bind("<Button-1>", lambda e, c=color: select_color(c, False))
            
            color_frame_latest = tk.Frame(latest_color_frame, width=30, height=30, bg=f'#{r:02x}{g:02x}{b:02x}', 
                                        relief="raised", bd=1)
            color_frame_latest.color_value = color
            color_frame_latest.pack(side="left", padx=5)
            color_frame_latest.bind("<Button-1>", lambda e, c=color: select_color(c, True))

def select_color(c, from_latest=False):
    global selected_color, selected_from_latest
    selected_color = c
    selected_from_latest = from_latest
    highlight_selected_swatch(c, from_latest)
    update_status_label()


def highlight_selected_swatch(color, from_latest=False):
    frame_to_check = latest_color_frame if from_latest else original_color_frame
    for widget in frame_to_check.winfo_children():
        if hasattr(widget, 'color_value') and widget.color_value == color:
            widget.config(relief="sunken", bd=5)
        else:
            widget.config(relief="raised", bd=1)


def pick_new_color():
    global new_rgb, selected_color
    if selected_color is None:
        messagebox.showinfo("Select Color", "Please select a color to change on the sprite.")
        return
    color = colorchooser.askcolor(title="Choose New Color")
    if color[0]:
        new_rgb = tuple(int(x) for x in color[0])
        apply_color_swap()


def color_change(img, pixels, new_rgb_values, old_rgb_values):
    global threshold, preserve_bw

    width, height = img.size
    old_r, old_g, old_b = old_rgb_values
    new_r, new_g, new_b = new_rgb_values
    thresh = threshold.get()
    preserve = preserve_bw.get()

    for x in range(width):
        for y in range(height):
            r, g, b, a = pixels[x, y]

            if (r, g, b) == old_rgb_values:
                pixels[x, y] = (*new_rgb_values, a)
                continue

            if preserve:
                is_black = r <= 10 and g <= 10 and b <= 10
                is_white = r >= 245 and g >= 245 and b >= 245
                if is_black or is_white:
                    continue

            distance = ((r - old_r)**2 + (g - old_g)**2 + (b - old_b)**2)**0.5
            # adjust lightness based on brightness ratio for the related color
            if distance <= thresh:
                brightness_old = (old_r + old_g + old_b) / 3
                brightness_pixel = (r + g + b) / 3
                brightness_ratio = brightness_pixel / brightness_old if brightness_old > 0 else 1

                adjusted_r = min(255, max(0, int(new_r * brightness_ratio)))
                adjusted_g = min(255, max(0, int(new_g * brightness_ratio)))
                adjusted_b = min(255, max(0, int(new_b * brightness_ratio)))

                pixels[x, y] = (adjusted_r, adjusted_g, adjusted_b, a)


def apply_color_swap():
    global modified_img, modified_pil, selected_color, new_rgb, selected_from_latest
    if selected_color is None or new_rgb is None:
        messagebox.showwarning("Missing", "Select a base color and new color first.")
        return

    undo_stack.append(modified_pil.copy())
    pixels = modified_pil.load()
    color_change(modified_pil, pixels, new_rgb, selected_color[:3])

    display_size = (250, 250)
    modified_img = ImageTk.PhotoImage(modified_pil.resize(display_size, Image.LANCZOS))
    modified_canvas.config(image=modified_img)

    old_color = selected_color
    new_color_with_alpha = (*new_rgb, selected_color[3] if len(selected_color) > 3 else 255)

    for widget in latest_color_frame.winfo_children():
        if hasattr(widget, 'color_value') and widget.color_value == old_color:
            widget.config(bg=f'#{new_rgb[0]:02x}{new_rgb[1]:02x}{new_rgb[2]:02x}')
            widget.color_value = new_color_with_alpha
            break


def update_status_label():
    if selected_color:
        r, g, b = selected_color[:3]
        palette_type = "edited" if selected_from_latest else "original"
        status_label.config(text=f"Selected {palette_type} color: RGB({r}, {g}, {b}). If the edited region is unsatisfactory, click undo, then change the gradient sensitivity.")
    else:
        status_label.config(text="No color selected")


def undo():
    global modified_pil, modified_img
    if not undo_stack:
        messagebox.showinfo("Undo", "Nothing to undo.")
        return
    modified_pil = undo_stack.pop()
    display_size = (250, 250)
    modified_img = ImageTk.PhotoImage(modified_pil.resize(display_size, Image.LANCZOS))
    modified_canvas.config(image=modified_img)
    extract_and_show_colors(modified_pil)
    update_status_label()


def save_image():
    if modified_pil is None:
        messagebox.showerror("Error", "No image to save.")
        return
    save_path = filedialog.asksaveasfilename(defaultextension=".png")
    if save_path:
        modified_pil.save(save_path)
        messagebox.showinfo("Saved", f"Sprite saved to {save_path}")


def main():
    #UI backbone was suggested by OpenAI, but I fine-tuned it to fit my needs
    global threshold, preserve_bw
    global original_canvas, modified_canvas
    global original_color_frame, latest_color_frame, status_label

    root = tk.Tk()
    root.title("Pixel Art Palette Swapper")
    root.geometry("850x600")
    root.configure(bg="#f0f0f0")

    threshold = tk.IntVar(value=30)
    preserve_bw = tk.BooleanVar(value=True)

    top_frame = tk.Frame(root, bg="#f0f0f0")
    palette_frame = tk.Frame(root, bg="#f0f0f0", relief="ridge", bd=2)
    top_frame.pack(side="top", fill="x", padx=20, pady=20)
    palette_frame.pack(fill="x", padx=20, pady=10)

    image_section = tk.Frame(top_frame, bg="#f0f0f0")
    buttons_section = tk.Frame(top_frame, bg="#f0f0f0")
    image_section.pack(side="left")
    buttons_section.pack(side="right", padx=20, fill="y")

    image_frame_left = tk.Frame(image_section, bg="#f0f0f0", relief="solid", bd=2, width=300, height=300)
    image_frame_right = tk.Frame(image_section, bg="#f0f0f0", relief="solid", bd=2, width=300, height=300)
    image_frame_left.pack(side="left", padx=10)
    image_frame_right.pack(side="left", padx=10)

    tk.Label(image_frame_left, text="Original Sprite", font=("Arial", 14)).pack(anchor="center")
    tk.Label(image_frame_right, text="Edited Sprite", font=("Arial", 14)).pack(anchor="center")

    original_canvas = tk.Label(image_frame_left)
    modified_canvas = tk.Label(image_frame_right)
    original_canvas.pack(padx=10, pady=10)
    modified_canvas.pack(padx=10, pady=10)

    tk.Button(buttons_section, text="Upload Sprite", width=15, command=upload_image).pack(pady=10)
    tk.Button(buttons_section, text="Pick New Color", width=15, command=pick_new_color).pack(pady=10)
    tk.Button(buttons_section, text="Undo", width=15, command=undo).pack(pady=10)
    tk.Button(buttons_section, text="Save Sprite", width=15, command=save_image).pack(pady=10)

    tk.Label(buttons_section, text="Sensitivity to Gradient", bg="#f0f0f0").pack(anchor="w", pady=(10, 5))
    tk.Scale(buttons_section, from_=0, to=100, orient='horizontal', variable=threshold,
             length=150, bg="#f0f0f0").pack(anchor="w")

    tk.Checkbutton(buttons_section, text="Preserve B/W", variable=preserve_bw, bg="#f0f0f0").pack(anchor="w", pady=5)

    tk.Label(palette_frame, text="Edited Sprite Palette (Clickable)", bg="#f0f0f0").pack(pady=(5, 0))
    latest_color_frame = tk.Frame(palette_frame, bg="#f0f0f0")
    latest_color_frame.pack(fill="x", pady=5)

    tk.Label(palette_frame, text="Original Sprite Palette (Clickable)", bg="#f0f0f0").pack(pady=(10, 0))
    original_color_frame = tk.Frame(palette_frame, bg="#f0f0f0")
    original_color_frame.pack(fill="x", pady=5)

    status_frame = tk.Frame(palette_frame, bg="#f0f0f0")
    status_frame.pack(fill="x", pady=5)
    status_label = tk.Label(status_frame, text="No color selected", bg="#f0f0f0", font=("Arial", 10))
    status_label.pack(side="left", padx=10)

    root.mainloop()


if __name__ == "__main__":
    main()
