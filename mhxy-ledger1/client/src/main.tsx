import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import { applyUiThemeToDocument, readBootstrapUiTheme } from './theme/uiTheme';
import './styles/global.css';
import './styles/themes-palettes.css';

applyUiThemeToDocument(readBootstrapUiTheme());

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
