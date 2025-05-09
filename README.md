# Gradient-Aware Pixel Art Palette Swapper
#### Description: 
This Python application streamlines the process of changing the colors of sprites used in video games by allowing users to simply pick colors directly from the sprite's palette to modify the corresponding areas. This application is especially helpful for non-artists who want to express their ideas visually. For example, fans of Pokemon can readily edit recolored Shiny (alternative color) Pokemon if they find the said Pokemon's color scheme undesirable. 

One of the main limitations in basic color swapping in images is the fact that sprites are rarely composed of just one specific color, as these often use a range of similar tones to depict depth and shading. This can lead to inconsistent results when non-artists attempt to recolor connected parts of the sprite that isn't exactly the same color as the main color picked by the user, like the fins on Garchomp's sprite.

To address this, I used a gradient sensitivity to consider colors that are similar enough to the selected color and adjusts them while preserving the relative light/dark balance. I also added a preserve B/W toggle to preserve true black and true white pixels which are often used for outlines in pixel art. As a result, the application is able to produce cleaner and more consistent sprite edits.

Users can export their work using the Save Sprite function, and an Undo button is available to roll back changes in case the selected replacement color doesn’t look quite right. A GUI was created by using the library tkinter to make this program more user friendly.

![Picture showing the layout of the application](https://i.ibb.co/b5gWhs3j/Screenshot-2025-05-09-163236.png)

