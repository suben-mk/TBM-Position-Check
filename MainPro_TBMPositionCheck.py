# MainProgram_TBM_PositionCheck
# By Suben Mukem
# Revision 03.08.2022

import numpy as np
import pandas as pd
from GeneralSurveyFunction import*

# -------------------------------------------- TBM Data -------------------------------------------- #

# TBM Axis
TBM_Pitch = -0.444831011303598 # mm/m
TBM_Roll = -1.40329714530813 # mm/m
TBM_Azimuth = 255.153954277529 # deg.

# TBM Excavation Direction
Excavation = "Backward" # Direction of excavation along with tunnel axis (Forward/Backward).

# Reference Points of TBM S-1073 at Front, Mid, Rear (Y, X, Z)
RefF = [0.000, 0.000, 0.000]
RefM = [0.000, -3.570, 0.000]
RefR = [0.000, -5.822, 0.000]

# Global coordinate of reference points for TBM S-1073 (P, E, N, Elev.)
df_GCRP = pd.read_excel("S-1073 Position Check.xlsx","Global Ref. Points")

# Local coordinate of reference Points for TBM S-1073 (P, Y, X, Z)
df_LCRP = pd.read_excel("S-1073 Position Check.xlsx","Local Ref. Points")

# Data of Tunnel Axis (Ch, E, N, Elev.)
df_DTA = pd.read_excel("S-1073 Position Check.xlsx","Tunnel Axis")

# ------------------------------------ Calculation of TBM Position ------------------------------------ #

# 1. Calculate global coordinate to center shield at front of TBM
TBM_Pitch = np.arctan(TBM_Pitch / 1000) * RadtoDeg 
TBM_Roll = np.arctan(TBM_Roll / 1000)  * RadtoDeg

# Linear (L) and Theta (Q) of local coordinate
L = np.where(df_GCRP.E == np.nan,
			 np.nan,
			 np.sqrt(df_LCRP.Y **2 + df_LCRP.Z **2)
			 )
Q = np.where(df_GCRP.E == np.nan,
			np.nan,
			abs(np.arctan(df_LCRP.Z / df_LCRP.Y) * RadtoDeg)
			)

# Y axis and Z axis After TBM Rolling
YR = L * np.cos((Q + TBM_Roll) * DegtoRad)
ZR = L * np.sin((Q + TBM_Roll) * DegtoRad)

# Global coordinate of center shield at front of TBM
EF, NF = np.where(df_LCRP.Y < 0,
                  CoorXYtoEN(df_GCRP.E, df_GCRP.N, TBM_Azimuth, abs(df_LCRP.X), YR),
                  CoorXYtoEN(df_GCRP.E, df_GCRP.N, TBM_Azimuth, abs(df_LCRP.X), -YR)
                 )
ELF = np.where(df_LCRP.Z < 0,
               (df_GCRP.Elev + ZR) + abs(df_LCRP.X) * np.tan(TBM_Pitch * DegtoRad),
               (df_GCRP.Elev - ZR) + abs(df_LCRP.X) * np.tan(TBM_Pitch * DegtoRad)
              )

# Center sheild result
'''
Cols = ["PointID", "Easting", "Northing", "Elevation", "dE", "dN", "dElev"]
CenterSheild = list(zip(df_GCRP.PointID, EF, NF, ELF, EF - np.nanmean(EF),
                   NF - np.nanmean(NF), ELF - np.nanmean(ELF)))
'''
Cols = ["PointID", "Actual E", "Actual N", "Actual Elev", "Y", "X", "Z","Transformed E", "Transformed N", "Transformed Elev", "dE", "dN", "dElev"]
CenterSheild = list(zip(df_GCRP.PointID, df_GCRP.E, df_GCRP.N, df_GCRP.Elev, df_LCRP.Y, df_LCRP.X, df_LCRP.Z,EF, NF, ELF, EF - np.nanmean(EF), NF - np.nanmean(NF), ELF - np.nanmean(ELF)))				   
df_CenterSheild = pd.DataFrame(CenterSheild, columns=Cols)
#df_CenterSheild.to_excel("TBM Position Check Result.xlsx", sheet_name="Center sheild result", index = False)

# 2. Calculate global coordinate of TBM at Front, Middle, Rear (E, N, Elev.)
# Front of TBM (Shield edge)
E_Front = np.nanmean(EF)
N_Front = np.nanmean(NF)
Elev_Front = np.nanmean(ELF)

# Middle of TBM (Shield articulation)
E_Middle, N_Middle = NextCoorENbyAziDist(E_Front, N_Front, TBM_Azimuth, RefM[1])
Elev_Middle = Elev_Front + abs(RefM[1]) * np.tan(-TBM_Pitch * DegtoRad)

# Rear of TBM (Target unit)
E_Rear, N_Rear = NextCoorENbyAziDist(E_Front, N_Front, TBM_Azimuth, RefR[1])
Elev_Rear = Elev_Front + abs(RefR[1]) * np.tan(-TBM_Pitch * DegtoRad)

# 3.Calculate chainage, horizontal deviation and vertical deviation of TBM
Rear = ["Target unit", E_Rear, N_Rear, Elev_Rear]
Middle = ["Shield articulation", E_Middle, N_Middle, Elev_Middle]
Front = ["Shield edge", E_Front, N_Front, Elev_Front]
Point_F = [Rear, Middle, Front]

# TBM excavation direction
DTA = df_DTA.to_numpy()
Deviation = []

for RP, EF, NF, ZF in Point_F:
	#Index point (A, B, C) from Tunnel Axis
	l = [] #distance from i to F 

	for ChTA, ETA, NTA, ZTA in DTA:	
		r = np.sqrt((ETA - EF)**2 + (NTA - NF)**2)
		l.append([r])

	B_pt = l.index(min(l)) #minimum distance position in array l[]
	Index_A = DTA[B_pt - 1] #Point A[C, E, N, Z] 
	Index_B = DTA[B_pt] #Point B[C, E, N, Z] (nearly)
	Index_C = DTA[B_pt + 1] #Point C[C, E, N, Z]

	#Distance AF, CF Azimuth AB, BC and Pitching AB, BC
	DireAF = Direction(Index_A[1], Index_A[2], EF, NF)
	DireCF = Direction(Index_C[1], Index_C[2], EF, NF)
	DireAB = Direction(Index_A[1], Index_A[2], Index_B[1], Index_B[2])
	DireBC = Direction(Index_B[1], Index_B[2], Index_C[1], Index_C[2])
	PitchAB = (Index_B[3] - Index_A[3]) / (Index_B[0] - Index_A[0])
	PitchBC = (Index_C[3] - Index_B[3]) / (Index_C[0] - Index_B[0])

	#Deviation of F point from Tunnel Axis
	if DireAF[0] < DireCF[0]:
		DevHz = CoorENtoXY(Index_B[1], Index_B[2], DireAB[1], EF, NF)
		ChF = Index_B[0] + DevHz[1]
		HzF = DevHz[0]
		VtF = ZF - (Index_B[3] + PitchAB * (ChF - Index_B[0]))
	else:
		DevHz = CoorENtoXY(Index_B[1], Index_B[2], DireBC[1], EF, NF)
		ChF = Index_B[0] + DevHz[1]
		HzF = DevHz[0]
		VtF = ZF - (Index_B[3] + PitchBC * (ChF - Index_B[0]))

	if Excavation == "Forward":
		Deviation.append([RP, ChF, HzF, VtF, EF, NF, ZF])
	else:
		Deviation.append([RP, ChF, -HzF, VtF, EF, NF, ZF])

# TBM position of transformed ref.points result
Names = [["Reference Position", "Chainage", "Hor.deviation", "Ver.deviation", "Easting", "Northing", "Elevation"]]
df_Names = pd.DataFrame(Names)
df_Deviation = pd.DataFrame(Deviation)
df_TBM_Position = pd.concat([df_Names.T, df_Deviation.T], axis=1)
df_TBM_Position.columns = df_TBM_Position.iloc[0]
#df_TBM_Position[1:].to_excel("TBM Position Check Result.xlsx", sheet_name="transformed ref.points", index = False)

# 4.Export TBM position Check Result
with pd.ExcelWriter("TBM Position Check Result.xlsx") as writer:
    df_CenterSheild.to_excel(writer, sheet_name="Center sheild", index = False)
    df_TBM_Position[1:].to_excel(writer, sheet_name="transformed ref.points", index = False)