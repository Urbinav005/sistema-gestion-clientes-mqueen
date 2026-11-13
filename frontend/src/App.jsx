// Tabla de rutas del sistema. Todo, menos el login, pide sesión
// y se muestra dentro del layout con la barra lateral.
import { Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout.jsx'
import RutaProtegida from './components/RutaProtegida.jsx'
import FormularioRefaccion from './pages/FormularioRefaccion.jsx'
import Inventario from './pages/Inventario.jsx'
import Login from './pages/Login.jsx'
import Proximamente from './pages/Proximamente.jsx'

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />

      {/* RN-13: solo el administrador con sesión entra a estas rutas */}
      <Route
        element={
          <RutaProtegida>
            <Layout />
          </RutaProtegida>
        }
      >
        <Route path="/" element={<Navigate to="/inventario" replace />} />
        <Route path="/inventario" element={<Inventario />} />
        <Route path="/inventario/nueva" element={<FormularioRefaccion />} />
        <Route path="/inventario/:id_pieza/editar" element={<FormularioRefaccion />} />
        <Route path="/resumen" element={<Proximamente titulo="Resumen" />} />
        <Route path="/clientes" element={<Proximamente titulo="Clientes" />} />
        <Route path="/citas" element={<Proximamente titulo="Citas" />} />
        <Route path="/vehiculos" element={<Proximamente titulo="Vehículos" />} />
      </Route>

      <Route path="*" element={<Navigate to="/inventario" replace />} />
    </Routes>
  )
}

export default App
