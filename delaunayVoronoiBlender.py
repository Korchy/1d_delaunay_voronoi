# import DelaunayVoronoi
import bpy

from .DelaunayVoronoi import computeVoronoiDiagram, computeDelaunayTriangulation
import bpy_extras
import bmesh


class Point:
	def __init__(self, x, y, z):
		self.x, self.y, self.z= x, y, z


def unique(L):
	"""Return a list of unhashable elements in s, but without duplicates.
	[[1, 2], [2, 3], [1, 2]] >>> [[1, 2], [2, 3]]"""
	# For unhashable objects, you can sort the sequence and then scan from the end of the list, deleting duplicates as you go
	nDupli=0
	nZcolinear=0
	L.sort()#sort() brings the equal elements together; then duplicates are easy to weed out in a single pass.
	last = L[-1]
	for i in range(len(L)-2, -1, -1):
		if last[:2] == L[i][:2]:#XY coordinates compararison
			if last[2] == L[i][2]:#Z coordinates compararison
				nDupli+=1#duplicates vertices
			else:#Z colinear
				nZcolinear+=1
			del L[i]
		else:
			last = L[i]
	return (nDupli,nZcolinear)#list data type is mutable, input list will automatically update and doesn't need to be returned


def checkEqual(lst):
	return lst[1:] == lst[:-1]


class ToolsPanelDelaunay(bpy.types.Panel):
	bl_category = "GIS"#Tab
	bl_label = "Delaunay Voronoi"
	bl_space_type = "VIEW_3D"
	# bl_context = "objectmode"
	bl_region_type = "TOOLS"

	def draw(self, context):
		self.layout.operator("delaunay.triangulation")
		self.layout.operator("voronoi.tesselation")

class OBJECT_OT_TriangulateButton(bpy.types.Operator):
	bl_idname = "delaunay.triangulation" #name used to refer to this operator (button)
	bl_label = "Triangulation" #operator's label
	bl_description = "Terrain points cloud Delaunay triangulation in 2.5D" #tooltip
	bl_options = {"UNDO"}

	def execute(self, context):
		#Get selected obj
		# objs = bpy.context.selected_objects
		# if len(objs) == 0 or len(objs)>1:
		# 	self.report({'INFO'}, "Selection is empty or too much object selected")
		# 	print("Selection is empty or too much object selected")
		# 	return {'FINISHED'}
		# obj = objs[0]

		obj = bpy.context.active_object

		if obj.type != 'MESH':
			self.report({'INFO'}, "Selection isn't a mesh")
			print("Selection isn't a mesh")
			return {'FINISHED'}
		#Get points coodinates
		#bpy.ops.object.transform_apply(rotation=True, scale=True)
		r = obj.rotation_euler
		s = obj.scale
		mesh = obj.data
		vertsPts = [vertex.co for vertex in mesh.vertices]
		vertsPts1 = [bpy_extras.object_utils.world_to_camera_view(bpy.context.scene, bpy.data.objects['Camera'], vertex.co) for vertex in mesh.vertices]
		#Remove duplicate
		verts= [[vert.x, vert.y, vert.z] for vert in vertsPts]
		verts1= [[vert.x, vert.y] for vert in vertsPts1]
		nDupli,nZcolinear = unique(verts)
		nVerts=len(verts)
		print(str(nDupli)+" duplicates points ignored")
		print(str(nZcolinear)+" z colinear points excluded")
		if nVerts < 3:
			self.report({'ERROR'}, "Not enough points")
			return {'FINISHED'}
		#Check colinear
		xValues=[pt[0] for pt in verts]
		yValues=[pt[1] for pt in verts]
		if checkEqual(xValues) or checkEqual(yValues):
			self.report({'ERROR'}, "Points are colinear")
			return {'FINISHED'}
		#Triangulate
		print("Triangulate "+str(nVerts)+" points...")
		vertsPts= [Point(vert[0], vert[1], vert[2]) for vert in verts]
		vertsPts1= [Point(vert[0], vert[1], None) for vert in verts1]
		# triangles=computeDelaunayTriangulation(vertsPts)
		triangles=computeDelaunayTriangulation(vertsPts1)
		triangles=[tuple(reversed(tri)) for tri in triangles]	#reverse point order --> if all triangles are specified anticlockwise then all faces up

		# print(triangles)

		bm = bmesh.new()
		# bm.from_mesh(mesh)
		bm = bmesh.from_edit_mesh(mesh)
		bm.verts.ensure_lookup_table()
		for triangle in triangles:
			v0 = bm.verts[triangle[0]]
			v1 = bm.verts[triangle[1]]
			v2 = bm.verts[triangle[2]]
			bm.faces.new([v0, v1, v2])
		bmesh.update_edit_mesh(mesh)
		bm.free()

		# print(str(len(triangles))+" triangles")
		# #Create new mesh structure
		# print("Create mesh...")
		# tinMesh = bpy.data.meshes.new("TIN") #create a new mesh
		# tinMesh.from_pydata(verts, [], triangles) #Fill the mesh with triangles
		# tinMesh.update(calc_edges=True) #Update mesh with new data
		# #Create an object with that mesh
		# tinObj = bpy.data.objects.new("TIN", tinMesh)
		# #Place object
		# bpy.ops.view3d.snap_cursor_to_selected()#move 3d-cursor
		# tinObj.location = bpy.context.scene.cursor_location #position object at 3d-cursor
		# tinObj.rotation_euler = r
		# tinObj.scale = s
		# #Update scene
		# bpy.context.scene.objects.link(tinObj) #Link object to scene
		# bpy.context.scene.objects.active = tinObj
		# tinObj.select = True
		# obj.select = False
		# #Report
		# self.report({'INFO'}, "Mesh created ("+str(len(triangles))+" triangles)")
		return {'FINISHED'}


class OBJECT_OT_VoronoiButton(bpy.types.Operator):
	bl_idname = "voronoi.tesselation" #name used to refer to this operator (button)
	bl_label = "Diagram" #operator's label
	bl_description = "Points cloud Voronoi diagram in 2D" #tooltip
	bl_options = {"REGISTER","UNDO"}#need register to draw operator options/redo panel (F6)
	#options
	meshType = bpy.props.EnumProperty(
		items = [("Edges", "Edges", ""), ("Faces", "Faces", "")],#(Key, Label, Description)
		name="Mesh type",
		description=""
		)

	"""
	def draw(self, context):
	"""

	def execute(self, context):
		#Get selected obj
		objs = bpy.context.selected_objects
		if len(objs) == 0 or len(objs)>1:
			self.report({'INFO'}, "Selection is empty or too much object selected")
			print("Selection is empty or too much object selected")
			return {'FINISHED'}
		obj = objs[0]
		if obj.type != 'MESH':
			self.report({'INFO'}, "Selection isn't a mesh")
			print("Selection isn't a mesh")
			return {'FINISHED'}
		#Get points coodinates
		r = obj.rotation_euler
		s = obj.scale
		mesh = obj.data
		vertsPts = [vertex.co for vertex in mesh.vertices]
		#Remove duplicate
		verts= [[vert.x, vert.y, vert.z] for vert in vertsPts]
		nDupli,nZcolinear = unique(verts)
		nVerts=len(verts)
		print(str(nDupli)+" duplicates points ignored")
		print(str(nZcolinear)+" z colinear points excluded")
		if nVerts < 3:
			self.report({'ERROR'}, "Not enough points")
			return {'FINISHED'}
		#Check colinear
		xValues=[pt[0] for pt in verts]
		yValues=[pt[1] for pt in verts]
		if checkEqual(xValues) or checkEqual(yValues):
			self.report({'ERROR'}, "Points are colinear")
			return {'FINISHED'}
		#Create diagram
		print("Tesselation... ("+str(nVerts)+" points)")
		xbuff, ybuff = 5, 5 # %
		zPosition=0
		vertsPts= [Point(vert[0], vert[1], vert[2]) for vert in verts]
		if self.meshType == "Edges":
			pts, edgesIdx = computeVoronoiDiagram(vertsPts, xbuff, ybuff, polygonsOutput=False, formatOutput=True)
		else:
			pts, polyIdx = computeVoronoiDiagram(vertsPts, xbuff, ybuff, polygonsOutput=True, formatOutput=True, closePoly=False)
		#
		pts=[[pt[0], pt[1], zPosition] for pt in pts]
		#Create new mesh structure
		print("Create mesh...")
		voronoiDiagram = bpy.data.meshes.new("VoronoiDiagram") #create a new mesh
		if self.meshType == "Edges":
			voronoiDiagram.from_pydata(pts, edgesIdx, []) #Fill the mesh with triangles
		else:
			voronoiDiagram.from_pydata(pts, [], list(polyIdx.values())) #Fill the mesh with triangles
		voronoiDiagram.update(calc_edges=True) #Update mesh with new data
		#create an object with that mesh
		voronoiObj = bpy.data.objects.new("VoronoiDiagram", voronoiDiagram)
		#place object
		bpy.ops.view3d.snap_cursor_to_selected()#move 3d-cursor
		voronoiObj.location = bpy.context.scene.cursor_location #position object at 3d-cursor
		voronoiObj.rotation_euler = r
		voronoiObj.scale = s
		#update scene
		bpy.context.scene.objects.link(voronoiObj) #Link object to scene
		bpy.context.scene.objects.active = voronoiObj
		voronoiObj.select = True
		obj.select = False
		#Report
		if self.meshType == "Edges":
			self.report({'INFO'}, "Mesh created ("+str(len(edgesIdx))+" edges)")
		else:
			self.report({'INFO'}, "Mesh created ("+str(len(polyIdx))+" polygons)")
		return {'FINISHED'}


def register():
	bpy.utils.register_class(ToolsPanelDelaunay)
	bpy.utils.register_class(OBJECT_OT_VoronoiButton)
	bpy.utils.register_class(OBJECT_OT_TriangulateButton)

def unregister():
	bpy.utils.unregister_class(OBJECT_OT_TriangulateButton)
	bpy.utils.unregister_class(OBJECT_OT_VoronoiButton)
	bpy.utils.unregister_class(ToolsPanelDelaunay)