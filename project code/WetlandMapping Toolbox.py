# -*- coding: utf-8 -*-
"""
Created on Thu Nov 18 10:47:33 2021

@author: jgerlitz
"""
import arcpy
from arcpy.ia import *
from arcpy.sa import *
import os

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "WetlandMapping Tool"
        self.alias = "WetlandMapping"

        # List of tool classes associated with this toolbox
        self.tools = [ExtractPointsModel]


class ExtractPointsModel(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "ExtractPointsModel"
        self.description = "This tool will create data for your 5 indices and extract them to randomly generated points"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
			displayName = "Output Workspace",
			name = "output_workspace",
			datatype = "DEWorkspace", 
			parameterType = "Required",
			direction = "Input")
         
        param1 = arcpy.Parameter(
            displayName = "Input DEM file",
            name =  "Input",
            datatype = "GPRasterLayer", 
            parameterType = "Required",
            direction = "Input")
        
        param2 = arcpy.Parameter(
			displayName = "Area of Interest Shapefile",
			name = "aoi_shape",
			datatype = ["DEShapefile","DEFeatureClass"],
			parameterType = "Required",
			direction = "Input")
        
        param3 = arcpy.Parameter(
			displayName = "Number of Random Points",
			name = "num_points",
			datatype = "GPString",
			parameterType = "Required",
			direction = "Input")

       


        params = [param0, param1, param2, param3]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
         # To allow overwriting outputs change overwriteOutput option to True.
        output_workspace = arcpy.GetParameterAsText(0)
        Input = arcpy.GetParameterAsText(1)
        aoi_shape = arcpy.GetParameterAsText(2)
        num_points = arcpy.GetParametersAsText(3)
        arcpy.env.workspace = output_workspace
        arcpy.env.overwriteOutput = False
    
        # Check out any necessary licenses.
        arcpy.CheckOutExtension("spatial")
        arcpy.CheckOutExtension("ImageAnalyst")
        arcpy.CheckOutExtension("3D")
    
        arcpy.ImportToolbox(r"c:\program files\arcgis\pro\Resources\ArcToolbox\toolboxes\Arc_Hydro_Tools_Pro.tbx")
        #Input = arcpy.Raster("harrison.tif")
        
        Name = os.path.basename(Input).rstrip(os.path.splitext(Input)[1])
        
        gdb = output_workspace
        shape = aoi_shape
    
    
        # Process: Create Random Points (Create Random Points) (management)
        rand_points = arcpy.management.CreateRandomPoints(out_path=gdb, out_name="rand_points", constraining_feature_class=shape, constraining_extent="0 0 250 250", number_of_points_or_field=num_points, minimum_allowed_distance="0 DecimalDegrees", create_multipoint_output="POINT", multipoint_size=0)[0]
    
        # Process: Focal Statistics (Focal Statistics) (ia)
        Elev_mean = gdb + "\\FocalSt_" + Name
        Focal_Statistics = Elev_mean
        Elev_mean = arcpy.ia.FocalStatistics(in_raster=Input, neighborhood="Circle 30 CELL", statistics_type="MEAN", ignore_nodata="DATA", percentile_value=90)
        Elev_mean.save(Focal_Statistics)
    
    
        # Process: Raster Calculator (Raster Calculator) (ia)
        TPI = gdb + "\\tpi_" + Name
        Raster_Calculator = TPI
        TPI =  Input - Elev_mean
        TPI.save(Raster_Calculator)
    
    
        # Process: Terrain Ruggedness Index (Terrain Ruggedness Index) (archydropro)
        TRI = gdb + "\\tri_" + Name
        arcpy.archydropro.terrainruggednessindex(Input_Terrain_Raster=Input, Output_Ruggedness_Raster=TRI)
        TRI = arcpy.Raster(TRI)
    
        # Process: Slope (Slope) (3d)
        slope = gdb + "Slope_" + Name
        arcpy.ddd.Slope(in_raster=Input, out_raster=slope, output_measurement="DEGREE", z_factor=1, method="PLANAR", z_unit="METER")
        slope = arcpy.Raster(slope)
        
        # Process: Calculate Topographic Wetness Index (TWI) (Calculate Topographic Wetness Index (TWI)) (archydropro)
        TWI = gdb + "twi_" + Name + ".tif"
        arcpy.archydropro.calculatetopographicwetnessindex(Input_Hydroconditioned_DEM=Input, Output_TWI_Raster=TWI, Save_Intermediate_Rasters=False, )
        TWI = arcpy.Raster(TWI)
        
        #slope_radians = slope * math.pi / 180.0
        # Process: Fill (Fill) (sa)
        DEM_filled = arcpy.sa.Fill(Input)
        
        # Process: Raster Calculator (2) (Raster Calculator) (ia)
        fill = gdb + "fill_" + Name
        Raster_Calculator_2 = fill
        fill =  Input - DEM_filled
        fill.save(Raster_Calculator_2)
    
        # Process: Extract Multi Values to Points (Extract Multi Values to Points) (sa)
        rand_points = arcpy.sa.ExtractMultiValuesToPoints(in_point_features=rand_points, in_rasters=[[TPI, "tpi"], [TRI, "tri"], [TWI, "twi"], [slope, "slope"], [fill, "fill"]], bilinear_interpolate_values="NONE").save(Extract_Multi_Values_to_Points)
        return rand_points