import { useState } from 'react'
import './App.css'

function App() {
  const [formData, setFormData] = useState({
    batterieVirtuelle: false,
    batteriePhysique: false,
    panneauxSolaires: ''
  })
  const [errors, setErrors] = useState({})
  const [submitted, setSubmitted] = useState(false)

  const handleCheckboxChange = (e) => {
    const { name, checked } = e.target

    setFormData(prev => {
      const newData = { ...prev }

      if (name === 'batterieVirtuelle' && checked) {
        newData.batterieVirtuelle = true
        newData.batteriePhysique = false
      } else if (name === 'batteriePhysique' && checked) {
        newData.batteriePhysique = true
        newData.batterieVirtuelle = false
      } else {
        newData[name] = checked
      }

      return newData
    })

    setErrors({})
    setSubmitted(false)
  }

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
    setErrors({})
    setSubmitted(false)
  }

  const validateForm = () => {
    const newErrors = {}

    if (formData.batterieVirtuelle && !formData.panneauxSolaires.trim()) {
      newErrors.panneauxSolaires = 'Veuillez spécifier les panneaux solaires pour une batterie virtuelle'
    }

    return newErrors
  }

  const handleSubmit = (e) => {
    e.preventDefault()

    const validationErrors = validateForm()

    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors)
      return
    }

    setSubmitted(true)
    console.log('Formulaire soumis:', formData)
  }

  return (
    <div className="container">
      <div className="card">
        <h1>Configuration Batterie</h1>

        <form onSubmit={handleSubmit}>
          <div className="form-section">
            <h2>Type de batterie</h2>

            <div className="checkbox-group">
              <label className={`checkbox-label ${formData.batterieVirtuelle ? 'checked' : ''}`}>
                <input
                  type="checkbox"
                  name="batterieVirtuelle"
                  checked={formData.batterieVirtuelle}
                  onChange={handleCheckboxChange}
                />
                <span className="checkbox-custom"></span>
                <span className="checkbox-text">Batterie virtuelle</span>
              </label>

              <label className={`checkbox-label ${formData.batteriePhysique ? 'checked' : ''}`}>
                <input
                  type="checkbox"
                  name="batteriePhysique"
                  checked={formData.batteriePhysique}
                  onChange={handleCheckboxChange}
                />
                <span className="checkbox-custom"></span>
                <span className="checkbox-text">Batterie physique</span>
              </label>
            </div>
          </div>

          <div className="form-section">
            <h2>Panneaux solaires</h2>
            <input
              type="text"
              name="panneauxSolaires"
              value={formData.panneauxSolaires}
              onChange={handleInputChange}
              placeholder="Ex: 12 panneaux 400W"
              className={errors.panneauxSolaires ? 'error' : ''}
            />
            {errors.panneauxSolaires && (
              <div className="error-message">
                {errors.panneauxSolaires}
              </div>
            )}
          </div>

          <button type="submit" className="submit-button">
            Valider
          </button>

          {submitted && Object.keys(errors).length === 0 && (
            <div className="success-message">
              Formulaire soumis avec succès !
            </div>
          )}
        </form>
      </div>
    </div>
  )
}

export default App
