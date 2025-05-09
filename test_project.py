from unittest.mock import MagicMock, patch
from PIL import Image
from project import load_image, upload_image, extract_and_show_colors, select_color, highlight_selected_swatch, pick_new_color, color_change, apply_color_swap, update_status_label, undo, save_image

def test_load_image():
    dummy_image = Image.new('RGBA', (100, 100))

    with patch('project.Image.open', return_value=dummy_image) as mock_open, \
         patch('project.ImageTk.PhotoImage', side_effect=lambda img: f"MockPhotoImage({img.width}x{img.height})") as mock_photo, \
         patch('project.extract_and_show_colors') as mock_extract, \
         patch('project.original_canvas', new=MagicMock()) as mock_orig_canvas, \
         patch('project.modified_canvas', new=MagicMock()) as mock_mod_canvas:

        load_image("dummy_path.png")

        mock_open.assert_called_once_with("dummy_path.png")
        assert mock_photo.call_count == 2
        mock_orig_canvas.config.assert_called_once()
        mock_mod_canvas.config.assert_called_once()
        mock_extract.assert_called_once_with(dummy_image)
    
def test_upload_image():
    with patch('project.filedialog.askopenfilename', return_value='test_image.png') as mock_dialog, \
        patch('project.load_image') as mock_load:
        
        upload_image()

        mock_dialog.assert_called_once()
        mock_load.assert_called_once_with('test_image.png')
    
    with patch('project.filedialog.askopenfilename', return_value='') as mock_dialog, \
         patch('project.load_image') as mock_load:
        
        upload_image()

        mock_dialog.assert_called_once()
        mock_load.assert_not_called()

def test_extract_and_show_colors():
    img = Image.new("RGBA", (10, 1))
    for i in range(10):
        img.putpixel((i, 0), (i*10, i*10, i*10, 255))

    dummy_colors = [(100, (i*10, i*10, i*10, 255)) for i in range(10)]

    with patch('project.original_color_frame', new=MagicMock()) as mock_orig_frame, \
         patch('project.latest_color_frame', new=MagicMock()) as mock_latest_frame, \
         patch('project.tk.Frame', side_effect=lambda *args, **kwargs: MagicMock()) as mock_tkframe, \
         patch.object(img, 'getcolors', return_value=dummy_colors):

        mock_orig_frame.winfo_children.return_value = [MagicMock(), MagicMock()]
        mock_latest_frame.winfo_children.return_value = [MagicMock()]

        extract_and_show_colors(img)

        assert all(w.destroy.called for w in mock_orig_frame.winfo_children.return_value)
        assert all(w.destroy.called for w in mock_latest_frame.winfo_children.return_value)

        assert mock_tkframe.call_count == 20 

def test_select_coloe():
    color = (100, 150, 200, 255)

    with patch('project.highlight_selected_swatch') as mock_highlight, \
         patch('project.update_status_label') as mock_status, \
         patch('project.selected_color', new=None), \
         patch('project.selected_from_latest', new=None):

        
        select_color(color, from_latest=True)
        # Check if the selected color swatch gets highlighted
        mock_highlight.assert_called_once_with(color, True)
        mock_status.assert_called_once()

def test_highlight_selected_swatch():
    target_color = (100, 150, 200, 255)

    matching_widget = MagicMock()
    matching_widget.color_value = target_color

    other_widget = MagicMock()
    other_widget.color_value = (50, 60, 70, 255)

    mock_children = [matching_widget, other_widget]

    with patch('project.original_color_frame', new=MagicMock()) as mock_orig_frame, \
         patch('project.latest_color_frame', new=MagicMock()) as mock_latest_frame:
        
        mock_orig_frame.winfo_children.return_value = mock_children
        mock_latest_frame.winfo_children.return_value = mock_children

        highlight_selected_swatch(target_color, from_latest=False)

        matching_widget.config.assert_called_with(relief="sunken", bd=5)
        other_widget.config.assert_called_with(relief="raised", bd=1)

        highlight_selected_swatch(target_color, from_latest=True)

        assert matching_widget.config.call_count == 2
        assert other_widget.config.call_count == 2

def test_pick_new_color():
    # No selected color shows error message
    with patch('project.selected_color', None), \
         patch('project.messagebox.showinfo') as mock_info:
        
        pick_new_color()

        mock_info.assert_called_once_with("Select Color", "Please select a color to change on the sprite.")
    # Valid color selection allows color swap
    with patch('project.selected_color', (100, 100, 100, 255)), \
         patch('project.colorchooser.askcolor', return_value=((255, 0, 0), "#ff0000")) as mock_chooser, \
         patch('project.apply_color_swap') as mock_apply, \
         patch('project.new_rgb', new=None):

        pick_new_color()

        mock_chooser.assert_called_once()
        mock_apply.assert_called_once()

def test_color_change():
    # Create a 3x1 image: red, black, near-red (should be threshold-matched)
    img = Image.new('RGBA', (3, 1))
    pixels = img.load()
    pixels[0, 0] = (255, 0, 0, 255)      # exact match
    pixels[1, 0] = (0, 0, 0, 255)        # black (should be preserved)
    pixels[2, 0] = (250, 5, 5, 255)      # near match, will be brightness-adjusted

    old_rgb = (255, 0, 0)
    new_rgb = (0, 255, 0)

    with patch('project.threshold', new=MagicMock(get=lambda: 10)), \
         patch('project.preserve_bw', new=MagicMock(get=lambda: True)):

        color_change(img, pixels, new_rgb, old_rgb)

    # Validate pixel updates
    assert pixels[0, 0] == (0, 255, 0, 255)              # exact match swapped
    assert pixels[1, 0] == (0, 0, 0, 255)                # black preserved
    r, g, b, a = pixels[2, 0]                            # near match, adjusted
    assert a == 255
    assert 0 <= r <= 255 and 100 <= g <= 255 and 0 <= b <= 255

def test_apply_color_swap():

    dummy_image = Image.new("RGBA", (10, 10), (100, 100, 100, 255))

    with patch('project.modified_pil', dummy_image), \
         patch('project.selected_color', (100, 100, 100, 255)), \
         patch('project.new_rgb', (0, 255, 0)), \
         patch('project.undo_stack', []), \
         patch('project.color_change') as mock_color_change, \
         patch('project.ImageTk.PhotoImage', return_value='MockedPhoto'), \
         patch('project.modified_canvas', new=MagicMock()) as mock_canvas, \
         patch('project.latest_color_frame', new=MagicMock()) as mock_frame:

        matching_widget = MagicMock()
        matching_widget.color_value = (100, 100, 100, 255)
        non_matching_widget = MagicMock()
        non_matching_widget.color_value = (50, 50, 50, 255)
        mock_frame.winfo_children.return_value = [non_matching_widget, matching_widget]

        apply_color_swap()
        mock_color_change.assert_called_once()

        # Check canvas image updated
        mock_canvas.config.assert_called_once_with(image='MockedPhoto')
        matching_widget.config.assert_called_once_with(bg='#00ff00')
        assert matching_widget.color_value == (0, 255, 0, 255)
    # Check if error message is shown when no color is selected
    with patch('project.selected_color', None), \
         patch('project.new_rgb', (255, 255, 255)), \
         patch('project.messagebox.showwarning') as mock_warn:
        apply_color_swap()
        mock_warn.assert_called_once_with("Missing", "Select a base color and new color first.")

def test_update_status_label():
    # With a selected color
    with patch('project.selected_color', (123, 45, 67, 255)), \
         patch('project.selected_from_latest', True), \
         patch('project.status_label', MagicMock()) as mock_label:

        update_status_label()
        mock_label.config.assert_called_once_with(
            text="Selected edited color: RGB(123, 45, 67). If the edited region is unsatisfactory, click undo, then change the gradient sensitivity."
        )
    # No selected color
    with patch('project.selected_color', None), \
         patch('project.status_label', MagicMock()) as mock_label:

        update_status_label()
        mock_label.config.assert_called_once_with(text="No color selected")

def test_undo():
    # Test when undo stack is empty
    with patch('project.undo_stack', []), \
         patch('project.messagebox.showinfo') as mock_info:
        undo()
        mock_info.assert_called_once_with("Undo", "Nothing to undo.")
    
    #test when undo stack is not empty
    dummy_image = Image.new("RGBA", (10, 10), (200, 100, 50, 255))

    with patch('project.undo_stack', [dummy_image.copy()]), \
         patch('project.modified_canvas', new=MagicMock()) as mock_canvas, \
         patch('project.ImageTk.PhotoImage', return_value='MockedPhoto'), \
         patch('project.extract_and_show_colors') as mock_extract, \
         patch('project.update_status_label') as mock_status, \
         patch('project.modified_pil', dummy_image):

        undo()

        # Ensure image is popped and updated
        mock_canvas.config.assert_called_once_with(image='MockedPhoto')
        mock_extract.assert_called_once()
        mock_status.assert_called_once()

def test_save_image():
    # No image
    with patch('project.modified_pil', None), \
         patch('project.messagebox.showerror') as mock_error:
        save_image()
        mock_error.assert_called_once_with("Error", "No image to save.")

    # Image exists and saves successfully
    dummy_image = Image.new("RGBA", (10, 10))

    with patch('project.modified_pil', dummy_image), \
         patch('project.filedialog.asksaveasfilename', return_value="test_output.png") as mock_ask, \
         patch('project.messagebox.showinfo') as mock_info, \
         patch.object(dummy_image, 'save') as mock_save:
        
        save_image()
        mock_save.assert_called_once_with("test_output.png")
        mock_info.assert_called_once_with("Saved", "Sprite saved to test_output.png")

    # Image exists but user cancels save dialog
    dummy_image = Image.new("RGBA", (10, 10))

    with patch('project.modified_pil', dummy_image), \
         patch('project.filedialog.asksaveasfilename', return_value="") as mock_ask, \
         patch('project.messagebox.showinfo') as mock_info, \
         patch.object(dummy_image, 'save') as mock_save:
        
        save_image()
        mock_save.assert_not_called()
        mock_info.assert_not_called()

