const { contextBridge, ipcRenderer } = require('electron');
contextBridge.exposeInMainWorld('client', {
  account: () => ipcRenderer.invoke('account'),
  liveStatus: () => ipcRenderer.invoke('live:status'),
  onLiveStatus: callback => {
    const listener = (_, connected) => callback(connected === true);
    ipcRenderer.on('live:status', listener);
    return () => ipcRenderer.removeListener('live:status', listener);
  },
  onLiveInvalidate: callback => {
    const listener = (_, event) => callback(event);
    ipcRenderer.on('live:invalidate', listener);
    return () => ipcRenderer.removeListener('live:invalidate', listener);
  },
  logout: () => ipcRenderer.invoke('logout'),
  api: args => ipcRenderer.invoke('api', args),
  getDraft: key => ipcRenderer.invoke('draft:get', key),
  setDraft: (key, source) => ipcRenderer.invoke('draft:set', key, source),
  openFile: () => ipcRenderer.invoke('file:open'),
  saveFile: (source, language) => ipcRenderer.invoke('file:save', source, language),
  run: args => ipcRenderer.invoke('run', args),
  openSite: route => ipcRenderer.invoke('open-site', route)
});
