from abaqus import *
from abaqus import getInputs
from abaqus import getInput
from abaqusConstants import *

import section
import regionToolset
import displayGroupMdbToolset as dgm
import part
import material
import assembly
import step
import interaction
import load
import mesh
import optimization
import job
import sketch
import visualization
import xyPlot
import displayGroupOdbToolset as dgo
import connectorBehavior

fields1 = (('cross_section: r(rectangle) ---- c(circle) ' , ''),('extrusion_depth: ', '100'))
cross_section , extrusion_depth = getInputs(fields = fields1 , label = 'Specify the values')

s = mdb.models['Model-1'].ConstrainedSketch(name='__profile__', sheetSize=100.0)
g, v, d, c = s.geometry, s.vertices, s.dimensions, s.constraints
s.setPrimaryObject(option=STANDALONE)

# Modifying the Sketch
if cross_section == 'r' or cross_section == 'rectangle':
    fields2 = (('length (meters): ', ' '), ('width (meters): ', ' ') )
    length , width = getInputs(fields = fields2 , label = 'Rectangle Dimensions')
    s.rectangle(point1=(-float(width)/2, float(length)/2), point2=(float(width)/2, -float(length)/2))
else:
    radius = float(getInput('circle radius (meters):' ))
    s.CircleByCenterPerimeter(center=(0.0, 0.0), point1=(0.0, radius))

p = mdb.models['Model-1'].Part(name='mainPart', dimensionality=THREE_D, type=DEFORMABLE_BODY)
p = mdb.models['Model-1'].parts['mainPart']
p.BaseSolidExtrude(sketch=s, depth= float(extrusion_depth))


# Material Selection
material_selected = getInput('Material: s(steel), a(aluminum)' )

if material_selected == 's' or material_selected == 'steel':
    mdb.models['Model-1'].Material(name='steel')
    mdb.models['Model-1'].materials['steel'].Elastic(table=((200000000000.0, 0.3),))
    mdb.models['Model-1'].HomogeneousSolidSection(name='main_section', material='steel', thickness=None)
else: 
    mdb.models['Model-1'].Material(name='aluminum')
    mdb.models['Model-1'].materials['aluminum'].Elastic(table=((69000000000.0, 0.3),))
    mdb.models['Model-1'].HomogeneousSolidSection(name='main_section', material='aluminum', thickness=None)

p = mdb.models['Model-1'].parts['mainPart']
c = p.cells
cells = c.getSequenceFromMask(mask=('[#1 ]', ), )
region = regionToolset.Region(cells=cells)
p = mdb.models['Model-1'].parts['mainPart']
p.SectionAssignment(region=region, sectionName='main_section', offset=0.0,offsetType=MIDDLE_SURFACE, offsetField='',thicknessAssignment=FROM_SECTION)

# Assembly Section
a = mdb.models['Model-1'].rootAssembly
    
a.DatumCsysByDefault(CARTESIAN)

p = mdb.models['Model-1'].parts['mainPart']
    
a.Instance(name='mainPart-1', part=p, dependent=ON)

# Step Creating
fields3 = (('Loading Time (s): ','1'),('initial increment: ','0.1'),('min proceeding increment (<= Initial Increment): ','0.1'),('max proceeding increment: ','1'))
duration, inInc, minIncrement, maxIncrement = getInputs(fields = fields3 , label = 'Duration, minInc and maxInc')

# Increment condition checking loop (initial increment must be less than or euqal to minInc)
while True:
    if float(inInc) >= float(minIncrement):
        break
    else:
        fields3 = (('Loading Time (s): ','1'),('initial increment: ','0.1'),('min proceeding increment (<= Initial Increment): ','0.1'),('max proceeding increment: ','1'))
        duration, inInc, minIncrement, maxIncrement = getInputs(fields = fields3 , label = 'Duration, minInc and maxInc')

mdb.models['Model-1'].StaticStep(name='static_analysis', previous='Initial', 
    timePeriod=float(duration), maxNumInc=1000000, initialInc=float(inInc), minInc=float(minIncrement), 
    maxInc=float(maxIncrement), nlgeom=ON)

# Boundary Condition e
if cross_section == 'c':
        # Encastre End
    a = mdb.models['Model-1'].rootAssembly
    f1 = a.instances['mainPart-1'].faces
    faces1 = f1.getSequenceFromMask(mask=('[#4 ]', ), )
    region = regionToolset.Region(faces=faces1)
    mdb.models['Model-1'].EncastreBC(name='Encastre_End', createStepName='Initial', region=region, localCsys=None)

    load_type = getInput('load type: p (pressure at the end), v(vertical load at the end)')   
        # Pressure Loading
    if load_type == 'p':
        a = mdb.models['Model-1'].rootAssembly
        s1 = a.instances['mainPart-1'].faces
        side1Faces1 = s1.getSequenceFromMask(mask=('[#2 ]', ), )
        region = regionToolset.Region(side1Faces=side1Faces1)
        pressure_magnitude = getInput('pressure magnitude (pa): ')
        mdb.models['Model-1'].Pressure(name='Load-1', createStepName='static_analysis', region=region, distributionType=UNIFORM, field='', magnitude=float(pressure_magnitude), amplitude=UNSET)
else:
        # Encastre End
    a = mdb.models['Model-1'].rootAssembly
    f1 = a.instances['mainPart-1'].faces
    faces1 = f1.getSequenceFromMask(mask=('[#20 ]', ), )
    region = regionToolset.Region(faces=faces1)
    mdb.models['Model-1'].EncastreBC(name='BC-1', createStepName='Initial', region=region, localCsys=None)

    load_type = getInput('load type: p (pressure at the end), v(vertical load at the end)')   
        # Pressure Loading
    if load_type == 'p':
        a = mdb.models['Model-1'].rootAssembly
        s1 = a.instances['mainPart-1'].faces
        side1Faces1 = s1.getSequenceFromMask(mask=('[#10 ]', ), )
        region = regionToolset.Region(side1Faces=side1Faces1)
        pressure_magnitude = getInput('pressure magnitude (pa): ')
        mdb.models['Model-1'].Pressure(name='Load-1', createStepName='static_analysis', region=region, distributionType=UNIFORM, field='', magnitude=float(pressure_magnitude), amplitude=UNSET)


# Meshing the Part
mesh_size = getInput('define the meshing size: c(coarse meshing), f(fine meshing), u(ultrafine meshine):')       
if cross_section == 'r':
    p = mdb.models['Model-1'].parts['mainPart']
    c = p.cells
    pickedRegions = c.getSequenceFromMask(mask=('[#1 ]', ), )
    p.setMeshControls(regions=pickedRegions, elemShape=TET, technique=FREE)
    elemType1 = mesh.ElemType(elemCode=C3D20R)
    elemType2 = mesh.ElemType(elemCode=C3D15)
    elemType3 = mesh.ElemType(elemCode=C3D10)
    p = mdb.models['Model-1'].parts['mainPart']
    c = p.cells
    cells = c.getSequenceFromMask(mask=('[#1 ]', ), )
    pickedRegions =(cells, )
    p.setElementType(regions=pickedRegions, elemTypes=(elemType1, elemType2, elemType3))
    p = mdb.models['Model-1'].parts['mainPart']
    if mesh_size == 'c':
        p.seedPart(size=float(width)/1, deviationFactor=0.1, minSizeFactor=0.1)
    elif mesh_size == 'f':
        p.seedPart(size=float(width)/5, deviationFactor=0.1, minSizeFactor=0.1)
    else:
        p.seedPart(size=float(width)/10, deviationFactor=0.1, minSizeFactor=0.1)
    p = mdb.models['Model-1'].parts['mainPart']
    p.generateMesh()
else:
    p = mdb.models['Model-1'].parts['mainPart']
    c = p.cells
    pickedRegions = c.getSequenceFromMask(mask=('[#1 ]', ), )
    p.setMeshControls(regions=pickedRegions, elemShape=TET, technique=FREE)
    elemType1 = mesh.ElemType(elemCode=C3D20R)
    elemType2 = mesh.ElemType(elemCode=C3D15)
    elemType3 = mesh.ElemType(elemCode=C3D10)
    p = mdb.models['Model-1'].parts['mainPart']
    c = p.cells
    cells = c.getSequenceFromMask(mask=('[#1 ]', ), )
    pickedRegions =(cells, )
    p.setElementType(regions=pickedRegions, elemTypes=(elemType1, elemType2, elemType3))
    p = mdb.models['Model-1'].parts['mainPart']
    if mesh_size == 'c':
        p.seedPart(size=float(radius)/1, deviationFactor=0.1, minSizeFactor=0.1)
    elif mesh_size == 'f':
        p.seedPart(size=float(radius)/5, deviationFactor=0.1, minSizeFactor=0.1)
    else:
        p.seedPart(size=float(radius)/10, deviationFactor=0.1, minSizeFactor=0.1)
    p = mdb.models['Model-1'].parts['mainPart']
    p.generateMesh()

# job Creation and CPU and GPU allocation
fields4 = (('cpu cores : ','1'),('gpu cores: ','1'))
cpu_numbers, gpu_numbers = getInputs(fields = fields4 , label = 'Define the number of cpu processors and gpu accelerations based on you hardware capability ')

a1 = mdb.models['Model-1'].rootAssembly
a1.regenerate()
a = mdb.models['Model-1'].rootAssembly

mdb.Job(name='main_analysis', model='Model-1', description='', type=ANALYSIS, atTime=None, waitMinutes=0, waitHours=0, queue=None, memory=90, 
    memoryUnits=PERCENTAGE, getMemoryFromAnalysis=True, 
    explicitPrecision=SINGLE, nodalOutputPrecision=SINGLE, echoPrint=OFF, 
    modelPrint=OFF, contactPrint=OFF, historyPrint=OFF, userSubroutine='', 
    scratch='', resultsFormat=ODB, numThreadsPerMpiProcess=1, 
    multiprocessingMode=DEFAULT, numCpus=int(cpu_numbers), numDomains=4, numGPUs=int(gpu_numbers))