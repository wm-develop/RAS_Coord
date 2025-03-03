# -*- coding: utf-8 -*-
# @Time    : 2025/2/27 下午8:34
# @Author  : wm
# @Software   : PyCharm
import os
import pandas as pd
from osgeo import ogr, osr


class CoordHandler:
    def __init__(self, result_path):
        self.result_path = result_path
        self.shapefile_path = os.path.join(self.result_path, 'demo2.shp')
        self.output_csv = pd.read_csv(os.path.join(self.result_path, 'output.csv'))
        self.geometries = []  # 存储几何对象和FID
        self.transformer = self.read_shapefile()

    def read_shapefile(self):
        """
        读取shp文件，进行坐标转换，提取所有features的GeometryRef和FID，记录在self.geometries中
        :return:
        """
        ds = ogr.Open(self.shapefile_path)
        if ds is None:
            return "无法打开shp文件"
        layer = ds.GetLayer()

        # 转换坐标
        source_srs = osr.SpatialReference()
        source_srs.ImportFromEPSG(4326)  # WGS 1984
        target_srs = osr.SpatialReference()
        target_srs.ImportFromEPSG(2436)  # Beijing_1954_3_Degree_GK_CM_117E
        transformer = osr.CoordinateTransformation(source_srs, target_srs)

        # 提取FID
        for feature in layer:
            geom = feature.GetGeometryRef().Clone()
            fid = feature.GetFID('FID')
            self.geometries.append((geom, fid))

        return transformer

    def check_finish(self):
        """
        检测上一次模拟是否正常结束
        :return:
        """
        log_path = os.path.join(self.result_path, 'server.log')
        try:
            with open(log_path, 'r') as f:
                last_line = ''
                for line in f:
                    last_line = line.rstrip('\n')
                if not last_line:
                    return False
                # 检查最后一行是否包含该字符串
                return '"POST /set_2d_hydrodynamic_data HTTP/1.1" 200 -' in last_line
        except IOError as e:
            return False

    def find_grid_id(self, x, y):
        """
        根据坐标对在`max_water_area.shp`查找对应的网格，在其属性表中读取网格的编号fid并返回
        :param x: x坐标，经度
        :param y: y坐标，纬度
        :return: 网格的编号fid
        """
        # 创建点对象并转换坐标
        point = ogr.Geometry(ogr.wkbPoint)
        point.AddPoint(x, y)

        try:
            point.Transform(self.transformer)
        except Exception as e:
            return "坐标转换失败"

        # 遍历所有几何体，查找对应的网格
        for geom, fid in self.geometries:
            if geom.Contains(point):
                return fid

        return None  # 未找到

    def find_flooding(self, fid):
        """
        根据fid查找对应列数据0变为任意值的对应行索引row_index并返回
        :param fid: 网格的编号
        :return: 对应行索引row_index
        """
        try:
            # 获取对应fid的列数据
            series = self.output_csv[fid]
        except KeyError:
            # 如果fid不存在，返回-1
            return -1

        # 遍历所有的时间步
        for i in range(1, len(series)):
            previous = series.iloc[i - 1]
            current = series.iloc[i]
            # 如果前一时刻该网格的水深为0（实际按<=0.005以避免模型计算精度问题）
            if previous <= 0.005 and current > 0:
                return i

        # 如果没找到符合条件的时间步，返回-1
        return -1

    def find_dam_water_depth(self, row_index):
        """
        根据row_index查找3个坝下网格对应的水位值并返回
        佛子岭：17367
        白莲崖：25497
        磨子潭：24832
        :param row_index: 淹没开始时刻对应的行索引值
        :return: 3个坝下网格对应的水位值
        """
        dam_fids = [17367, 25497, 24832]
        # 检查row_index是否合法
        if row_index >= len(self.output_csv) or row_index < 0:
            return "时间步不合法"

        try:
            values = []
            for fid in dam_fids:
                # 获取对应fid列的数据，然后取row_index行的值
                value = self.output_csv[fid].iloc[row_index]
                values.append(value)
            # 返回佛子岭、白莲崖、磨子潭水深组成的三元组
            return tuple(values)
        except KeyError as e:
            return f"错误：FID {e} 不存在于结果文件中"
