"""
TreeView Class

This class represents an instance of the Passive Tree for a given Build.
Multiple Trees can exist in a single Build (at various progress levels;
  at different Jewel/Cluster itemizations, etc.)

A Tree instance is tied to a Version of the Tree as released by GGG and thus older Trees
  need to be supported for backwards compatibility reason.
"""

from PySide6.QtCore import QLineF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QPen, QPainter, QPixmap
from PySide6.QtWidgets import QFrame, QGraphicsEllipseItem, QGraphicsScene, QGraphicsView, QDialogButtonBox

from ui.PoB_Main_Window import Ui_MainWindow
from PoB.constants import ColourCodes, class_backgrounds, Layers, PlayerClasses
from PoB.settings import Settings
from PoB.build import Build
from dialogs.popup_dialogs import MasteryPopup
from widgets.tree_graphics_item import TreeGraphicsItem
from PoB.utils import _debug, html_colour_text, print_call_stack


class TreeView(QGraphicsView):
    def __init__(self, _settings: Settings, _build: Build, _win: Ui_MainWindow) -> None:
        """
        Initialize Treeview
        :param _settings: pointer to Settings()
        :param _build: pointer to build()
        :param _win: A pointer to MainWindowUI
        """
        super(TreeView, self).__init__()
        self.win = _win
        self.settings = _settings
        self.build = _build

        self.search_rings = []
        self.active_nodes = []
        self.active_lines = []
        self.compare_nodes_items = []

        self._scene = QGraphicsScene()
        self.setScene(self._scene)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFrameShape(QFrame.NoFrame)
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        # set a background of black as this stops the tree looking ugly when a non-dark theme is selected.
        # ascendancy-background-3.jpg also has a hard coded black background.
        self.setBackgroundBrush(QBrush(Qt.black, Qt.SolidPattern))

        self._char_class_bkgnd_image = None
        self.fitInView(True, 0.1)

        self.setDragMode(QGraphicsView.ScrollHandDrag)
        # Stop the drag icon being the default, which the above line would do
        self.viewport().setCursor(Qt.ArrowCursor)

        # A list of jewels that the tree_view can use for showing the correct image
        self.items_jewels = {}
        # add_tree_images needs to be before adding a margin
        self.add_tree_images(True)

        # add a margin to make panning the view seem more comfortable
        rect = self.sceneRect()
        rect.adjust(-1000.0, -1000.0, 1000.0, 1000.0)
        self.setSceneRect(rect)

    # Inherited, don't change definition
    def wheelEvent(self, event):
        """
        Zoom in and out. Attempt to limit zoom
        :param event:
        :return:
        """
        if event.angleDelta().y() > 0:
            factor = 1.25
        else:
            factor = 0.8
        self.fitInView(True, factor)
        event.accept()

    # Inherited, don't change definition
    def enterEvent(self, event) -> None:
        """
        Override the GraphicsView drag cursor
        :param event: Internal event matrix
        :return: N/A
        """
        super(TreeView, self).enterEvent(event)
        self.viewport().setCursor(Qt.ArrowCursor)

    # Inherited, don't change definition
    def mousePressEvent(self, event) -> None:
        """
        Override the GraphicsView drag cursor
        :param event: Internal event matrix
        :return: N/A
        """
        # _debug("tree_view: mousePressEvent")
        super(TreeView, self).mousePressEvent(event)
        # Stop hand cursor
        self.viewport().setCursor(Qt.ArrowCursor)

    # Inherited, don't change definition
    def mouseReleaseEvent(self, event) -> None:
        """
        Turn on or off a node if one is clicked on. Update node count appropriately.
        Trigger a mastery effect popup when appropriate

        :param event: Internal event matrix.
        :return: N/A
        """
        # _debug("tree_view: mouseReleaseEvent")
        super(TreeView, self).mouseReleaseEvent(event)
        # Ensure hand cursor is gone (it's sneaky)
        self.viewport().setCursor(Qt.ArrowCursor)
        # If compare is on, then the compare circles will be the first item detected (highest in the Z order)
        # Get all items at that pos and find the first TreeGraphicsItem
        graphic_items = self.items(event.pos())
        if len(graphic_items) < 1:
            return
        # for i in graphic_items:
        #     if type(i) is TreeGraphicsItem:
        #         print(f"{i.node_id=}, {i.name=}")
        g_item: TreeGraphicsItem = next((i for i in graphic_items if isinstance(i, TreeGraphicsItem)), None)
        if (
            g_item
            and type(g_item) is TreeGraphicsItem
            and g_item.node_id != 0
            and not g_item.node_isAscendancyStart
            and g_item.node_classStartIndex < 0
        ):
            # print("mouseReleaseEvent", g_item.node_id)
            if event.button() == Qt.LeftButton:
                if g_item.node_id in self.build.current_spec.nodes:
                    if g_item.node_type == "Mastery":
                        self.build.current_spec.remove_mastery_effect(g_item.node_id)
                    # elif g_item.node_type == "Socket":
                    #     del self.build.current_spec.sockets[g_item.node_id]
                    self.build.current_spec.remove_node(g_item.node)
                else:
                    node = g_item.node
                    # Check to see if node is connected to an active node
                    for node_id in node.nodes_out.union(node.nodes_in):
                        if node_id in self.build.current_spec.nodes:
                            if g_item.node_type == "Mastery":
                                # print("mastery_popup", self.build.current_tree.nodes[g_item.node_id])
                                m_effect = self.mastery_popup(self.build.current_tree.nodes[g_item.node_id])
                                if m_effect != 0:
                                    self.build.current_spec.add_node(g_item.node)
                                    g_item.build_tooltip(m_effect)
                            elif g_item.node_type == "Socket":
                                # ToDo: Do we need a popup to select a jewel ?
                                self.build.current_spec.add_node(g_item.node)
                            else:
                                # print(f"mouseReleaseEvent, {g_item.node_type=}")
                                self.build.current_spec.add_node(g_item.node)
                            break
            elif event.button() == Qt.RightButton:
                # look for Mastery and popup a dialog
                # print("RightButton", _item.node_type)
                if g_item.node_type == "Mastery" and g_item.node_id in self.build.current_spec.nodes:
                    self.mastery_popup(self.build.current_tree.nodes[g_item.node_id])
            self.add_tree_images()
            # count the new nodes ...
            self.build.count_allocated_nodes()
            # ... and display them
            self.win.display_number_node_points(-1)
            self.win.do_calcs()

    # Function Overridden
    def fitInView(self, scale=True, factor=None):
        """
        Part of the zoom facility.
        :param scale: Not used.
        :param factor: Scale factor.
        :return: N/A
        """
        current_scale_factor = self.transform().m11()
        # Limit Zoom by reversing the factor if needed
        if current_scale_factor > 1.0:
            factor = 0.8
        if current_scale_factor < 0.08:
            factor = 1.25
        if factor is None:
            unity = self.transform().mapRect(QRectF(0, 0, 1, 1))
            self.scale(1 / unity.width(), 1 / unity.height())
        else:
            self.scale(factor, factor)

    def mastery_popup(self, node):
        """
        Popup a list of mastery effects for this node and set the currect spec with the choice, if needed.

        :param node: node(): this mastery
        :return: bool: effect id if one was chosen
        """
        dlg = MasteryPopup(
            self.settings._app.tr,
            node,
            self.build.current_spec,
            self.build.current_tree.mastery_effects_nodes[node.name],
            self.win,
        )
        # 0 is discard, 1 is save
        _return = dlg.exec()
        if _return:
            self.build.current_spec.add_mastery_effect(node.id, dlg.selected_effect)
        return _return and dlg.selected_effect or 0

    def add_picture(self, pixmap, x, y, z=0, _node=None, selectable=False):
        """
        Add a picture or pixmap
        :param pixmap: string or pixmap to be added.
        :param x: it's position in the scene.
        :param y: it's position in the scene.
        :param z: Layers: which layer to use: -2: background, -1: connectors, etc
        :param _node:Node(): The affiliated node
        :param selectable:bool: Selectable
        :return: ptr to the created TreeGraphicsItem
        """
        if pixmap is None or pixmap == "":
            print(f"tree_view.add_picture called with wrong information. pixmap: {pixmap},  x:{x}, y: {y}")
            return None
        image = TreeGraphicsItem(self.settings, pixmap, _node, z, selectable)
        image.setPos(x, y)
        self._scene.addItem(image)
        return image

    def switch_class(self, _class):
        """
        Changes for this Class() to deal with a PoB class change. ToDo: Is this needed.
        :param _class:
        :return: N/A
        """
        # if self.build.current_tree.char_class != _class
        # Alert for wiping your tree
        # self.build.current_tree.char_class = _class
        # self.build.current_class = _class
        return True

    def switch_tree(self, full_clear=False):
        """
        Changes for this Class() to deal with a PoB tree change.
        :param: full_clear: bool: If set, delete the tree images also. If not set, only delete the active images
        :return: N/A
        """
        self.add_tree_images(full_clear)
        self.refresh_search_rings()

    def refresh_search_rings(self):
        """
        clear and redraw search rings around nodes.

        :return: N/A
        """

        def add_circle(_image: TreeGraphicsItem, colour, line_width=10, z_value=10):
            """
            Draw a circle around an overlay image.

            :param _image: TreegraphicsItem: The image to have a circle drawn around it.
            :param colour: ColourCodes.value: yep.
            :param line_width: int: yep.
            :param z_value: Layers: which layer shall we draw it.
            :return: a reference to the circle.
            """
            _circle = QGraphicsEllipseItem(
                _image.pos().x() + _image.offset().x() - line_width / 2,
                _image.pos().y() + _image.offset().y() - line_width / 2,
                _image.width + line_width,
                _image.height + line_width,
            )
            _circle.setPen(QPen(QColor(colour), line_width, Qt.SolidLine))
            _circle.setZValue(z_value)
            # _circle.setStartAngle(90 * 16)
            # _circle.setSpanAngle(90 * 16)

            return _circle
            # add_circle

        for item in self.search_rings:
            self._scene.removeItem(item)
            del item
        self.search_rings.clear()
        if self.build.search_text == "":
            return
        # We only put search rings around a node's overlay, not the node itself.
        # This stops the ring appearing under or over the node's overlay.
        for image in self.build.current_tree.graphics_items:
            if image.node_isoverlay and self.build.search_text in image.build_tooltip():
                circle = add_circle(image, Qt.yellow, 12)
                self.search_rings.append(circle)
                self._scene.addItem(circle)

    def add_tree_images(self, full_clear=False):
        """
        Used when swapping tree's in a build.
        It will remove all assets, including selected nodes and connecting lines and present an empty tree.
        It is expected another function will be called to created selected nodes and connecting lines.
        :param: full_clear: bool: If set, delete the tree images also. If not set, only delete the active images
        :return: N/A
        """

        def add_compare_spot(_node, colour, z_value=10):
            """
            Draw a filled circle an image.

            :param _node: Node: The node whose image is to have a circle drawn on it.
            :param colour: ColourCodes.value: yep.
            :param z_value: Layers: which layer shall we draw it.
            :return: a reference to the circle.
            """
            _image = _node.inactive_overlay_image is None and _node.inactive_image or _node.inactive_overlay_image
            _spot = QGraphicsEllipseItem(
                _image.pos().x() + _image.offset().x(),
                _image.pos().y() + _image.offset().y(),
                _image.width,
                _image.height,
            )
            _spot.setBrush(QBrush(colour, Qt.SolidPattern))
            _spot.setOpacity(0.3)
            _spot.setZValue(z_value)
            _spot.setAcceptedMouseButtons(Qt.NoButton)
            self.compare_nodes_items.append(_spot)
            self._scene.addItem(_spot)

            return _spot
            # add_compare_spot

        # leave the print in till we have everything working.
        # It is what tells us how often the assets are being redrawn.
        # _debug(f"add_tree_images, full_clear={full_clear}")
        if self.build.current_tree is None:
            return

        tree = self.build.current_tree
        # do not use self.clear as it deletes the graphics assets from memory
        if full_clear:
            # don't delete the images for the nodes as they are owned by the relevant Tree() class.
            for g_item in self.items():
                self._scene.removeItem(g_item)

            # Add inactive tree assets
            for image in tree.graphics_items:
                self._scene.addItem(image)

            # Add inactive tree lines
            for line in tree.lines:
                self._scene.addItem(line)

            # Hack to draw class background art, the position data isn't in the tree JSON.
            if self.build.current_class != PlayerClasses.SCION:
                bkgnd = class_backgrounds[self.build.current_class]
                self._char_class_bkgnd_image = self.add_picture(
                    QPixmap(f":/Art/TreeData/{bkgnd['n']}"), bkgnd["x"], bkgnd["y"], Layers.backgrounds
                )
                self._char_class_bkgnd_image.filename = bkgnd["n"]
        else:
            # don't delete the images for the nodes as they are owned by the relevant Tree() class.
            # Remove active tree assets
            for item in self.active_nodes:
                if item is not None:
                    self._scene.removeItem(item)
            # Remove active tree lines
            for item in self.active_lines:
                self._scene.removeItem(item)
                del item
            # Remove search rings
            for item in self.compare_nodes_items:
                self._scene.removeItem(item)
                del item
        self.active_nodes.clear()
        self.active_lines.clear()
        self.compare_nodes_items.clear()

        # loop though active nodes and add them and their connecting lines
        lines_db = {}
        active_nodes = self.build.current_spec.nodes
        for node_id in active_nodes:
            node = tree.nodes.get(node_id, None)
            if node is not None:
                if node.active_image is not None:
                    self.active_nodes.append(node.active_image)
                    self.active_nodes.append(node.active_overlay_image)
                    self._scene.addItem(node.active_image)
                    if node.active_overlay_image is not None:
                        self._scene.addItem(node.active_overlay_image)
                if node.masteryEffects:
                    node.activeEffectImage.build_tooltip(self.build.current_spec.get_mastery_effect(node_id))
                    self.active_nodes.append(node.activeEffectImage)
                    self._scene.addItem(node.activeEffectImage)
                if node.type == "Socket":
                    jewels = self.build.current_spec.sockets
                    image = None
                    if self.items_jewels and node.id in jewels.keys():
                        jewel_node_id = jewels[node.id]
                        # if jewel_node_id != 0:
                        jewel_item = self.items_jewels.get(jewel_node_id, None)
                        if jewel_item:
                            sprite = node.sprites.get(jewel_item.sub_type, None)
                            if sprite is not None:
                                image = self.add_picture(sprite["handle"], node.x, node.y, Layers.jewels, node, True)
                                image.setOffset(sprite["ox"], sprite["oy"])
                                image.item = jewel_item
                    if image:
                        self.active_nodes.append(image)
                    self.active_nodes.append(node.active_overlay_image)
                    self._scene.addItem(node.active_overlay_image)

                # Draw active lines
                if node.type not in ("ClassStart", "Mastery"):
                    in_out_nodes = []
                    for other_node_id in node.nodes_out.union(node.nodes_in) & active_nodes:
                        other_node = tree.nodes.get(other_node_id, None)
                        if (
                            other_node is not None
                            and other_node.type not in ("ClassStart", "Mastery")
                            # This stops lines crossing out of the Ascendancy circles
                            and node.ascendancyName == other_node.ascendancyName
                        ):
                            in_out_nodes.append(other_node)

                    for other_node in in_out_nodes:
                        # check if we have this line already
                        ids = sorted([node.id, other_node.id])
                        index = f"{ids[0]}_{ids[1]}"
                        if not lines_db.get(index, False):
                            lines_db[index] = True
                            line = self.scene().addLine(
                                node.x,
                                node.y,
                                other_node.x,
                                other_node.y,
                                QPen(QColor(ColourCodes.CURRENCY.value), 4),
                            )
                            line.setAcceptTouchEvents(False)
                            line.setAcceptHoverEvents(False)
                            line.setZValue(Layers.active_connectors)
                            self.active_lines.append(line)

        # Darken Ascendancy backgrouds.
        current_ascendancy = f"Classes{self.build.ascendClassName}"
        for item in tree.ascendancy_group_list:
            # Chieftain is brighter than the rest
            dim = item.filename == "ClassesChieftain" and 0.3 or 0.5
            if current_ascendancy == item.filename:
                item.setOpacity(1.0)
            else:
                item.setOpacity(dim)

        # Draw spots for comparing trees
        if self.win.tree_ui.check_Compare.isChecked() and self.build.compare_spec is not None:
            current = set(self.build.current_spec.nodes)
            nodes_not_in_compare_spec = [x for x in self.build.compare_spec.nodes if x not in current]
            for node in nodes_not_in_compare_spec:
                add_compare_spot(tree.nodes[node], Qt.green, 6)

            compare = set(self.build.compare_spec.nodes)
            nodes_not_in_current_spec = [x for x in self.build.current_spec.nodes if x not in compare]
            for node in nodes_not_in_current_spec:
                add_compare_spot(tree.nodes[node], Qt.red, 6)
            # Can add lines too. How to find the node that connects back to an active node ?
            # Possibly add all active and difference nodes ?
            # Add them to Layers.connectors-1 ? To have the active lines overwrite them
        # add_tree_images
