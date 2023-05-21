import { useState } from 'react';
import jsonData from './plugins_metadata.json';
import { Link, Route, Routes } from 'react-router-dom';
import { useParams } from 'react-router-dom';
import Logo from './assets/logo-white-text.svg'
import './App.css'

function App() {

  return (
    <>
    <div>
        <a href="/aiida-registry/">
          <img src={Logo} className="logo" alt="aiida logo" />
        </a>

    </div>
    <div>
      <Routes>
        <Route path="/aiida-registry/" element={<MainIndex />} />
        <Route path="/aiida-registry/details/:key" element={<Details />} />
      </Routes>
    </div>
    </>
  );
}

function MainIndex() {
  return (
    <div>
      {Object.entries(jsonData).map(([key, value]) => (
        <div key={key}>
          <Link to={`/aiida-registry/details/${key}`}><h3>{key}</h3></Link>
          <p>{value.development_status}</p>
          <p>{value.aiida_version}</p>
          <p>{value.metadata.description}</p>
          <a href={value.code_home}>Source Code</a><br></br>
          <a href={value.documentation_url}>Documentation</a>
        </div>
      ))}
    </div>
  );
}

function Details() {
  const { key } = useParams();
  const value = jsonData[key];

  return (
    <>
    <h2>
        AiiDA plugin package &quot;<a href={value.code_home}>{value.name}</a>&quot;
    </h2>
    <p><a href="/aiida-registry/">&lt; back to the registry index</a></p>
    <h2>General information</h2>
    <div>
      <p>
          <strong>Short description</strong>: { value.metadata.description }
      </p>

      <p>
          <strong>How to install</strong>: <code>{value.pip_url}</code>
      </p>

      <p>
          <strong>Source code</strong>: <a href={ value.code_home } target="_blank">Go to the source code repository</a>
      </p>

      <p>
          <strong>Documentation</strong>: <a href={value.documentation_url} target="_blank">Go to plugin documentation</a>
      </p>
    </div>

    <h2>Detailed information</h2>
    <div>
      <p>
          <strong>Author(s)</strong>: { value.metadata.author }
      </p>
      <p>
          <strong>Contact</strong>: <a href={`mailto:${ value.metadata.author_email }`}>{ value.metadata.author_email }</a>
      </p>

      <p>
          <strong>How to use from python</strong>: <code>import { value.package_name }</code>
      </p>
      <p>
          <strong>Most recent version</strong>: { value.metadata.version }
      </p>
      </div>
    </>
  );
}

export default App;