#-*-coding:UTF-8 -*-
import arcpy
import math

inputFeature = r'F:\地表异常\A制图综合触发机制\test\南京水系100.shp'
arcpy.env.workspace = r'F:\地表异常\A制图综合触发机制\test\100'

#最小外接矩形  其中saveSize是指最终图片的大小，单位是MB
def minBound(filename,saveSize):
    outminBound = arcpy.env.workspace +'/minBound.shp'
    #创建要素的包络矩形,为什么不能添加集合属性
    arcpy.MinimumBoundingGeometry_management(filename,outminBound,'ENVELOPE','ALL')
    #添加集几何属性
    arcpy.AddGeometryAttributes_management(outminBound,'EXTENT')
    #计算包络矩形的长宽比
    listf = []
    listf =  arcpy.da.SearchCursor(outminBound,['EXT_MIN_X','EXT_MAX_X','EXT_MIN_Y','EXT_MAX_Y'])
    for i in listf:
        minx,maxx,miny,maxy=i[0],i[1],i[2],i[3]
    w = maxx-minx
    l = maxy-miny
    #根据长宽比计算像素数
    save_bit = saveSize*(2**20)*0.8
    width = int(math.sqrt(save_bit*(w/l)))
    length = int(width*l/w)
    returnList = [length,width,minx,maxx,miny,maxy]
    print(returnList)
    return returnList

minBoundList = minBound(inputFeature,3)

#创建渔网
def create_fishnet(filename,extList):
    outputFile = arcpy.env.workspace + '/pyfishnet.shp'
    originCoordinate = str(extList[2]) +' '+ str(extList[4])
    yAxisCoordinate = str(extList[2]) +' '+ str(extList[5])
    opsitionCoorner = str(extList[3]) +' '+ str(extList[5])
    print(originCoordinate,yAxisCoordinate,opsitionCoorner)
    labels = 'NO_LABELS'
    geometryType = 'POLYGON'
    arcpy.CreateFishnet_management(outputFile,originCoordinate,yAxisCoordinate,0,0,extList[0],extList[1],opsitionCoorner,labels,filename,geometryType)
    print('create fishnet finished')
create_fishnet(inputFeature,minBoundList)


#按位置选择
#首先给渔网添加一个字段
def selectByLocation(fishnet,sourceFeature):  #第一个参数是上一步生成的渔网，第二个参数是指最初的输入feature，也就是需要进行判断的数据
    arcpy.AddField_management(fishnet,'state','SHORT')
    print('add field finished')
    #按位置选择,首先需要把这些数据变成featurelayer
    arcpy.MakeFeatureLayer_management(fishnet,'fishnet_lyr')

    arcpy.SelectLayerByLocation_management('fishnet_lyr','intersect',sourceFeature)
    select_fishnet = arcpy.env.workspace +'/select_fishnet.shp'
    #按属性选择的图层是一个临时图层，需要复制成一个数据
    arcpy.CopyFeatures_management('fishnet_lyr','select_fishnet')
    arcpy.CalculateField_management(select_fishnet,'state','1')
    print('selectByLocation finished')
    return select_fishnet
Sfishnet =selectByLocation(arcpy.env.workspace + '/pyfishnet.shp',inputFeature)

#转为栅格进行地图载负量分析

cellSize = (minBoundList[3]-minBoundList[2])/minBoundList[1]
def con_featureToRaster(Sfishnet):
    outRaster = arcpy.env.workspace + '/outraster.tif'
    outStasticRaster = arcpy.env.workspace + '/StasticRaster.tif'
    arcpy.FeatureToRaster_conversion(Sfishnet,'state',outRaster,cellSize)
    print('conversion finished')
    outFocalRaster = arcpy.sa.FocalStatistics(outRaster,arcpy.sa.NbrRectangle(4, 4, "CELL"),'SUM','')
    outFocalRaster.save(outStasticRaster)
con_featureToRaster(Sfishnet)

