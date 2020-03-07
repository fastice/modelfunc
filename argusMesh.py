# -*- coding: utf-8 -*-
"""
Created on Wed Apr  4 14:33:23 2018

@author: ian
"""
from utilities import myerror


class argusMesh:
    # nodes
    def __init__(self, expFile=None, meshType='Triangle'):
        self.nNodes, self.nElements = 0, 0
        self.nodes, self.elements = [], []
        self.elSize = {1: 2, 2: 3, 3: 4}
        self.nodeValues, self.elementValues = [], []
        self.nNVal, self.nEVal = 0, 0
        self.nodeIndex, self.elIndex = [], []
        self.meshpy = None
        self.elementType = []
        self.tag, self.group = [], []
        self.meshtype = meshType
        if expFile is not None:
            self.readExp(expFile)

    def readGmshHeader(self, gmshFile):
        ''' read gmsh header, return pointer to start of nodes'''
        try:
            fpGmsh = open(gmshFile, 'r')
        except Exception:
            myerror(f'error opening gmsh input file {gmshFile}')
        for line in fpGmsh:
            if '$Nodes' in line:
                return fpGmsh
        myerror(f'Reached end of {gmshFile} with no $Nodes found')

    def readGmshNodes(self, fpGmsh):
        ''' read nodes from a gmsh file '''
        try:
            nNewNodes = int(fpGmsh.readline().strip())
        except Exception:
            myerror('readGmshNodes: cannot parse nLines')
        #
        nodeIndex, nodesRead = len(self.nodeIndex), 0
        for line in fpGmsh:
            nodeData = [eval(x) for x in line.split()]
            self.nodes.append(nodeData[1:3])
            self.nodeValues.append(nodeData[3])
            nodeIndex += 1  # Increment node index and append
            self.nodeIndex.append(nodeIndex)
            nodesRead += 1  # Increment node counter
            if nodesRead == nNewNodes:
                print(f'Read {nodesRead} nodes')
                self.nNodes += nodesRead
                break
        if nodesRead != nNewNodes:
            myerror(f'readGmshNodes: expected {nNewNodes} nodes read '
                    f'{nodesRead}')
        if '$EndNodes' not in fpGmsh.readline():
            myerror(f'readGmshNodes: expected $EendNodes')

    def readGmshElements(self, fpGmsh):
        ''' read elements from a gmsh file '''
        try:
            print(f'{fpGmsh.readline()}')
            nNewElements = int(fpGmsh.readline().strip())
        except Exception:
            myerror('readGmshElements: cannot parse nLines')
        #
        elIndex, elRead = len(self.elIndex), 0
        for line in fpGmsh:
            elData = [eval(x) for x in line.split()]
            self.elements.append(elData[5:])
            self.elementType.append(elData[1])
            self.tag.append(elData[3])
            self.group.append(elData[4])
            elIndex += 1  # Increment el index and append
            self.elIndex.append(elIndex)
            elRead += 1  # Increment el counter
            if elRead == nNewElements:
                print(f'Read {elRead} elements')
                self.nElements += elRead
                break
        if elRead != nNewElements:
            myerror(f'readGmshElements: expected {nNewElements} nodes read '
                    f'{elRead}')
        if '$EndElements' not in fpGmsh.readline():
            myerror(f'readGmshNodes: expected $EndElements')

    def readGmsh(self,gmshFile):
        '''Read gmsh file'''
        fpGmsh = self.readGmshHeader(self, gmshFile)
        self.readGmshNodes(fpGmsh)
        
    def parseHeader(self, fpExp):
        ''' Parse header info from argus exp file'''
        headerPieces = fpExp.readline().split()
        #
        if len(headerPieces) != 4:
            myerror('header not found')
        # parse header
        nNewNodes = int(headerPieces[1])
        nNewElements = int(headerPieces[0])
        self.nNVal = int(headerPieces[3])
        self.nEVal = int(headerPieces[2])
        self.nodeValues = [[] for i in range(self.nNVal)]
        self.elementValues = [[] for i in range(self.nEVal)]
        print(f'Header info {nNewNodes} {nNewElements} '
              f'{self.nNVal} {self.nEVal}')
        return nNewNodes, nNewElements

    def parseNodes(self, fpExp, nNewNodes):
        ''' Parse nodal values from argus exp file'''
        nodesRead = 0
        nodeIndex = len(self.nodeIndex)
        self.nodeOffset = len(self.nodeIndex)
        for line in fpExp:
            if line.isspace():
                continue
            pieces = line.split()
            if pieces[0] == 'N':
                # Append coordinates for a point
                self.nodes.append((float(pieces[2]), float(pieces[3])))
                # parse node data values
                self.nodeValues.append([float(pieces[4+i])
                                        for i in range(self.nNVal)])
                nodeIndex += 1  # Increment node index and append
                self.nodeIndex.append(nodeIndex)
                nodesRead += 1  # Increment node counter
                if nodesRead == nNewNodes:
                    print(f'Read {nodesRead} nodes')
                    self.nNodes += nodesRead
                    return nodesRead
        if nodesRead != self.nNodes:
            myerror(f'Expected {nNewNodes} nodes but only read {nodesRead}')
    
    def getNewTag(self):
        ''' Get a new incremental tag '''
        if len(self.tag) == 0:
            return 1  # First tag
        else:
            return self.tag[-1] + 1  # Increment last tag
        
    def parseElements(self, fpExp, nNewElements, elTag=None, elType=2):
        ''' Parse Elements from an argus export file '''
        # Loop through line
        if elTag is None:
            elTag = self.getNewTag()
        elementsRead = 0
        elementIndex = len(self.elIndex)
        for line in fpExp:
            pieces = line.split()
            if pieces[0] == 'E':
                # Read indices with node increment if needed
                self.elements.append([int(pieces[i+2]) + self.nodeOffset
                                      for i in range(self.elSize[elType])])
                # Read values for element
                for i in range(0, self.nEVal):
                    self.elementValues[i].append(
                        [int(pieces[i+5]) for i in range(self.nEVal)])
                self.elementType.append(elType)
                elementIndex += 1
                self.elIndex.append(elementIndex)
                self.tag.append(elTag)
                self.group.append(1000)
                elementsRead += 1
                if elementsRead == nNewElements:
                    print(f'Read {elementsRead} elements')
                    self.nElements += elementsRead
                    return elementsRead
        #
        if elementsRead != self.nEVal:
            myerror(
                f'Expected {nNewElements} elements but found {elementsRead}')

    def readExp(self, expFile, elTag=None, elType=2):
        ''' Read Argus export (.exp) file'''
        # open file
        try:
            fpExp = open(expFile, 'r')
        except Exception:
            myerror('argusMesh.readExp: could not open meshfile for read')
        #
        nNewNodes, nNewElements = self.parseHeader(fpExp)
        # Nodes
        nodesRead = self.parseNodes(fpExp, nNewNodes)
        # Elements
        elementsRead = self.parseElements(fpExp, nNewElements,
                                          elTag=elTag, elType=elType)
        print(nodesRead, self.nNodes, elementsRead, self.nElements)
        fpExp.close()
        return

    def gmshHeader(self, gmshFile):
        ''' Open gmsh file and write header'''
        # open file
        try:
            fpGmsh = open(gmshFile, 'w')
        except Exception:
            myerror(f'error opening gmsh output file {gmshFile}')
        # Header info
        print('$MeshFormat', file=fpGmsh)
        print('2.2 0 8', file=fpGmsh)
        print('$EndMeshFormat', file=fpGmsh)
        return fpGmsh

    def writeGmshNodes(self, fpGmsh):
        ''' write node data '''
        print('$Nodes', file=fpGmsh)
        print(self.nNodes, file=fpGmsh)
        #
        for i in range(self.nNodes):
            print(f'{self.nodeIndex[i]:10} {self.nodes[i][0]:15.5f} '
                  f'{self.nodes[i][1]:15.5f} 0.0 ', file=fpGmsh)
        print('$EndNodes', file=fpGmsh)

    def writeGmshElements(self, fpGmsh):
        ''' write node data '''
        print('$Elements', file=fpGmsh)
        print(self.nElements, file=fpGmsh)
        for i in range(self.nElements):
            # [rint(self.elements[i])
            if self.elementType[i] > 1:
                group = 1000
            else :
                group=self.elIndex[i]
            print(f'{self.elIndex[i]:8} {self.elementType[i]:3} 2 '
                  f'{self.tag[i]:4} {self.group[i]:6} '
                  f'{"".join([f"{x:10}" for x in self.elements[i]])}',
                  file=fpGmsh)
        print('$EndElements', file=fpGmsh)

    def toGmsh(self, gmshFile):
        ''' Write msh in gmsh format '''
        #
        # init
        fpGmsh = self.gmshHeader(gmshFile)
        # Nodes
        self.writeGmshNodes(fpGmsh)
        #
        # Elements
        self.writeGmshElements(fpGmsh)
        #
        fpGmsh.close()

        # #
        # # Node data
        # print('$NodeData',file=fp)
        # # string tag
        # print(1,file=fp)
        # print('"Argus Node data"',file=fp)
        # # 1 dummy real tag
        # print(1,file=fp)
        # print(0.0,file=fp)
        # # integer tags
        # print(3,file=fp)
        # print(0,file=fp) # dummy time step
        # print(self.nNVal,file=fp) # number of values per node
        # print(self.nNodes,file=fp) # number of nodes; assume all
        # data=np.array(self.nodeValues)
        # for i in range(1,self.nNodes+1) :
        #     print(i,*data[:,i-1] ,file=fp)
        # print('$EndNodeData',file=fp)
        # #
        # # Element data
        # print('$ElementData',file=fp)
        # # string tag
        # print(1,file=fp)
        # print('"Argus Element data"',file=fp)
        # # 1 dummy real tag
        # print(1,file=fp)
        # print(0.0,file=fp)
        # # integer tags
        # print(3,file=fp)
        # print(0,file=fp) # dummy time step
        # print(self.nEVal,file=fp) # number of values per elements
        # print(self.nElements,file=fp) # number of elements; assume all
        # dataE=np.array(self.elementValues)
        # for i in range(1,self.nElements+1) :
        #     print(i,*dataE[:,i-1] ,file=fp)
        # print('$EndNodeData',file=fp)    
        
    #    def addPolyNodes(self, xyPoly):
    #     ''' Add coords from poly to node list'''
    #     nodeIndex = len(self.nodeIndex)
    #     firstNode = nodeIndex+1
    #     self.nodeOffset = len(self.nodeIndex)
    #     nodesRead = 0
    #     nNewNodes = xyPoly.shape[0]
    #     for xy in xyPoly:
    #         print(xy)
    #         self.nodes.append((xy[0], xy[1]))
    #         # parse node data values
    #         self.nodeValues.append([0]*self.nNVal)
    #         nodeIndex += 1  # Increment node index and append
    #         self.nodeIndex.append(nodeIndex)
    #         nodesRead += 1  # Increment node counter
    #         if nodesRead == nNewNodes:
    #             print(f'Read {nodesRead} nodes')
    #             self.nNodes += nodesRead
    #             return firstNode, nodesRead
    #     if nodesRead != nNewNodes:
    #         myerror(f'Expected {nNewNodes} nodes but only read {nodesRead}')

    # def getNewTag(self):
    #     ''' Get a new incremental tag '''
    #     if len(self.tag) == 0:
    #         return 1  # First tag
    #     else:
    #         return self.tag[-1] + 1  # Increment last tag

    # def addPolyElements(self, firstNode, nNodes):
    #     ''' Create elements from node to node+1 for polyline '''
    #     elIndex = len(self.elIndex)
    #     self.elOffset = len(self.elIndex)
    #     elRead = 0
    #     nNewElements = nNodes-1
    #     elTag = self.getNewTag()
    #     #
    #     # loop over nNodes-1 elements
    #     for i in range(firstNode, firstNode + nNewElements):
    #         self.elements.append([i, i+1])
    #         # parse node data values
    #         self.elementValues.append([0]*self.nEVal)
    #         elIndex += 1  # Increment node index and append
    #         self.elIndex.append(elIndex)
    #         self.tag.append(elTag)
    #         self.elementType.append(1)
    #         elRead += 1  # Increment node counter
    #         if elRead == nNewElements:
    #             print(f'Read {elRead} elements')
    #             self.nElements += elRead
    #             return elRead
    #     if elRead != nNewElements:
    #         myerror(f'Expected {nNewElements} nodes but only read {elRead}')

    # def readDomainShapes(self, shapeFile):
    #     ''' Read a domain poly line and add it to the node and element list '''
    #     # open shape file
    #     shape = shapefile.Reader(shapeFile)
    #     #
    #     # Loop over each feature in shape file
    #     for feature in shape.shapeRecords():
    #         # extract polygon from feature
    #         poly = feature.shape.__geo_interface__
    #         xyPoly = np.array(poly['coordinates'])
    #         xyPoly = self.checkClockWise(xyPoly)
    #         print(xyPoly.shape)
    #         firstNode, nNodes = self.addPolyNodes(xyPoly)
    #         self.addPolyElements(firstNode, nNodes)
            
            