const fs = require('fs')

const baseURL = 'https://pokeapi.co/api/v2/'
const speciesURL = baseURL + 'pokemon-species/'

async function fetchEvolutionChain(evolutionURL) {
  console.log("fetching chain for " + evolutionURL)
  const response = await fetch(evolutionURL)
  const data = await response.json()
  const chain = data.chain
  const evolutions = []

  function extractEvolutions(chain) {
    evolutions.push(chain.species.name)
    if (chain.evolves_to.length > 0) {
      chain.evolves_to.forEach(evolution => extractEvolutions(evolution))
    }
  }

  extractEvolutions(chain)
  return evolutions
}

async function fetchPokemonSpecies() {
  const response = await fetch(speciesURL + '?limit=10000') // Fetch all Pokémon species
  const data = await response.json()
  return data.results
}

async function createEvolutionDictionary() {
  const speciesList = await fetchPokemonSpecies()
  const evolutionDict = {}

  for (const species of speciesList) {
    const speciesResponse = await fetch(species.url)
    const speciesData = await speciesResponse.json()
    const evolutionChainURL = speciesData.evolution_chain.url
    const evolutions = await fetchEvolutionChain(evolutionChainURL)

    evolutions.forEach((pokemon, index) => {
      if (!evolutionDict[pokemon]) {
        evolutionDict[pokemon] = evolutions.slice(index)
      }
    })
  }

  return evolutionDict
}

async function main() {
  const evolutionDict = await createEvolutionDictionary()
  fs.writeFileSync('evolutionDict.json', JSON.stringify(evolutionDict, null, 2))
  console.log('Evolution dictionary created and saved to evolutionDict.json')
}

main().catch(console.error)
