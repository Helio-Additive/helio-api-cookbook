"""
GraphQL query and mutation constants for the Helio Additive API.

These queries are extracted from BambuStudio's HelioDragon.cpp and define
the full set of operations available through the Helio GraphQL endpoint.
"""

QUERY_PRESIGNED_URL = """
query getPresignedUrl($fileName: String!) {
  getPresignedUrl(fileName: $fileName) {
    mimeType
    url
    key
  }
}
"""

MUTATION_CREATE_GCODE = """
mutation CreateGcode($input: CreateGcodeInputV2!) {
  createGcodeV2(input: $input) {
    id
    name
    sizeKb
    status
    progress
  }
}
"""

QUERY_POLL_GCODE = """
query GcodeV2($id: ID!) {
  gcodeV2(id: $id) {
    id
    name
    sizeKb
    status
    progress
    errors
    errorsV2 {
      line
      type
    }
  }
}
"""

MUTATION_CREATE_SIMULATION = """
mutation CreateSimulation($input: CreateSimulationInput!) {
  createSimulation(input: $input) {
    id
    name
    progress
    status
    gcode { id name }
    printer { id name }
    material { id name }
    reportJsonUrl
    thermalIndexGcodeUrl
    estimatedSimulationDurationSeconds
    insertedAt
    updatedAt
  }
}
"""

QUERY_POLL_SIMULATION = """
query Simulation($id: ID!) {
  simulation(id: $id) {
    id
    name
    progress
    status
    thermalIndexGcodeUrl
    printInfo {
      printOutcome
      printOutcomeDescription
      temperatureDirection
      temperatureDirectionDescription
      caveats {
        caveatType
        description
      }
    }
    speedFactor
    suggestedFixes {
      category
      extraDetails
      fix
      orderIndex
    }
  }
}
"""

MUTATION_CREATE_OPTIMIZATION = """
mutation CreateOptimization($input: CreateOptimizationInput!) {
  createOptimization(input: $input) {
    id
    name
    progress
    status
    gcode { id name }
    printer { id name }
    material { id name }
    insertedAt
    updatedAt
  }
}
"""

QUERY_POLL_OPTIMIZATION = """
query Optimization($id: ID!) {
  optimization(id: $id) {
    id
    name
    progress
    status
    optimizedGcodeWithThermalIndexesUrl
    qualityStdImprovement
    qualityMeanImprovement
  }
}
"""

QUERY_PRINTERS = """
query GetPrinters($page: Int) {
  printers(page: $page, pageSize: 20) {
    pages
    pageInfo { hasNextPage }
    objects {
      ... on Printer {
        id
        name
        alternativeNames { bambustudio }
      }
    }
  }
}
"""

QUERY_MATERIALS = """
query GetMaterials($page: Int) {
  materials(page: $page, pageSize: 20) {
    pages
    pageInfo { hasNextPage }
    objects {
      ... on Material {
        id
        name
        feedstock
        alternativeNames { bambustudio }
      }
    }
  }
}
"""

QUERY_PRINT_PRIORITY_OPTIONS = """
query GetPrintPriorityOptions($materialId: ID!) {
  printPriorityOptions(materialId: $materialId) {
    value
    label
    isAvailable
    description
  }
}
"""

QUERY_USER_QUOTA = """
query GetUserRemainingOpts {
  user {
    remainingOptsThisMonth
    addOnOptimizations
    isFreeTrialActive
    isFreeTrialClaimed
    subscription { name }
  }
  freeTrialEligibility
}
"""

QUERY_DEFAULT_OPT_SETTINGS = """
query DefaultOptimizationSettings($gcodeId: ID!) {
  defaultOptimizationSettings(gcodeId: $gcodeId) {
    minVelocity
    maxVelocity
    minVelocityIncrement
    minExtruderFlowRate
    maxExtruderFlowRate
    tolerance
    maxIterations
    reductionStrategySettings {
      strategy
      autolinearDoCriticality
      autolinearDoFitness
      autolinearDoInterpolation
      autolinearCriticalityMaxNodesDensity
      autolinearCriticalityThreshold
      autolinearFitnessMaxNodesDensity
      autolinearFitnessThreshold
      autolinearInterpolationLevels
      linearNodesLimit
    }
    residualStrategySettings {
      strategy
      exponentialPenaltyHigh
      exponentialPenaltyLow
    }
    layersToOptimize {
      fromLayer
      toLayer
    }
    optimizer
  }
}
"""

QUERY_RECENT_RUNS = """
query GetRecentRuns {
  optimizations {
    objects {
      ... on Optimization {
        id
        name
        status
        optimizedGcodeWithThermalIndexesUrl
        qualityMeanImprovement
        qualityStdImprovement
        gcode {
          gcodeUrl
          gcodeKey
          material { id name }
          printer { id name }
          numberOfLayers
          slicer
        }
      }
    }
  }
  simulations {
    objects {
      ... on Simulation {
        id
        name
        status
        thermalIndexGcodeUrl
        gcode {
          gcodeUrl
          gcodeKey
          material { id name }
          printer { id name }
          numberOfLayers
          slicer
        }
        printInfo {
          printOutcome
        }
      }
    }
  }
}
"""

# NOTE: This query is not used by BambuStudio. The API accepts it but
# thermal histories require Helio to enable the feature for your account.
# This is an enterprise feature mainly used for advanced R&D/material science.
# Contact Helio Additive if downloads return 404 errors.
QUERY_THERMAL_HISTORIES = """
query ThermalHistories($isOptimized: Boolean!, $layer: Int!, $optimizationId: ID!) {
  thermalHistories(isOptimized: $isOptimized, layer: $layer, optimizationId: $optimizationId) {
    assetType
    url
  }
}
"""

# Query to get mesh URL from a simulation
QUERY_SIMULATION_MESH = """
query SimulationMesh($id: ID!) {
  simulation(id: $id) {
    meshUrl {
      assetType
      url
    }
  }
}
"""

# Query to get mesh URLs from an optimization (both original and optimized)
QUERY_OPTIMIZATION_MESH = """
query OptimizationMesh($id: ID!) {
  optimization(id: $id) {
    optimizedMeshAsset {
      assetType
      url
    }
    originalMeshAsset {
      assetType
      url
    }
  }
}
"""
