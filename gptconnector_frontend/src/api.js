import axios from 'axios'

const BASE_URL = 'https://680fd8632b8b-5410392378761838076.ngrok-free.app/gptconnector/'
const axiosConfig = axios.create({
  baseURL: BASE_URL,
  headers: {
    common: {
      AuthorizationToken: 'it-is-really-secret-key'
    }
  }
})

const callApi = async (method, url, params) => {
  const response = await axiosConfig.request({
    method, url, [method === 'get' ? 'params' : 'data']: params || {},
  })
  return response.data
}

export default {
  async saveApiKey({api_key}) {
    return await callApi('get', '/save_api_key/', {api_key})
  },
}
