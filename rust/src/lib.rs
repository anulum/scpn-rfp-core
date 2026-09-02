// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// SCPN RFP Core — native level-0 physics kernels

//! Native level-0 device-physics kernels of SCPN RFP Core.
//!
//! Every function mirrors one closed-form evaluation of the pure-Python
//! floor in `scpn_rfp_core.physics` with the identical operation order,
//! so the IEEE-754 double results agree bit for bit. The kernels use only
//! `+`, `-`, `*` and `/` (all correctly rounded) plus the vendored Bessel
//! functions `J0` and `J1` of the shared kernel library crate
//! (`scpn-reactor-kernels-rs`, pinned by commit in `Cargo.toml` and in the
//! manifest), which the Python floor evaluates through the same library.
//! Nothing here solves an equation and no value describes a real machine;
//! the design records are ADR 0005 and ADR 0006 of the repository.

pub mod profiles;
pub mod relaxation;

pub use scpn_reactor_kernels_native::numerics::transcendental::NumericsError;

#[cfg(feature = "python")]
mod python {
    use pyo3::exceptions::PyValueError;
    use pyo3::prelude::*;

    fn numerics(err: crate::NumericsError) -> PyErr {
        PyValueError::new_err(err.to_string())
    }

    /// Reversal parameter of the model, see `crate::relaxation::bfm_reversal_parameter`.
    #[pyfunction]
    fn bfm_reversal_parameter(theta: f64) -> PyResult<f64> {
        crate::relaxation::bfm_reversal_parameter(theta).map_err(numerics)
    }

    /// Relaxed-state tuple, see `crate::relaxation::relaxed_state`.
    #[pyfunction]
    #[allow(clippy::type_complexity)]
    fn relaxed_state(
        minor_radius_m: f64,
        theta: f64,
        average_toroidal_field_t: f64,
        declared_reversal_parameter: f64,
        plasma_current_ma: f64,
    ) -> PyResult<(
        f64,
        f64,
        f64,
        f64,
        f64,
        f64,
        bool,
        Option<f64>,
        f64,
        f64,
        f64,
    )> {
        let s = crate::relaxation::relaxed_state(
            minor_radius_m,
            theta,
            average_toroidal_field_t,
            declared_reversal_parameter,
            plasma_current_ma,
        )
        .map_err(numerics)?;
        Ok((
            s.pinch_parameter,
            s.force_free_parameter_per_m,
            s.axis_field_t,
            s.bfm_reversal_parameter,
            s.declared_reversal_parameter,
            s.reversal_mismatch,
            s.reversed,
            s.reversal_radius_m,
            s.edge_poloidal_field_bfm_t,
            s.edge_poloidal_field_current_t,
            s.edge_field_relative_mismatch,
        ))
    }

    /// Radial station tuple, see `crate::profiles::radial_station`.
    #[pyfunction]
    fn radial_station(
        fraction: f64,
        minor_radius_m: f64,
        major_radius_m: f64,
        theta: f64,
        axis_field_t: f64,
    ) -> PyResult<(f64, f64, f64, f64, f64)> {
        let s = crate::profiles::radial_station(
            fraction,
            minor_radius_m,
            major_radius_m,
            theta,
            axis_field_t,
        )
        .map_err(numerics)?;
        Ok((
            s.fraction,
            s.radius_m,
            s.toroidal_field_t,
            s.poloidal_field_t,
            s.safety_factor,
        ))
    }

    /// Python module `scpn_rfp_native`.
    #[pymodule]
    fn scpn_rfp_native(m: &Bound<'_, PyModule>) -> PyResult<()> {
        m.add_function(wrap_pyfunction!(bfm_reversal_parameter, m)?)?;
        m.add_function(wrap_pyfunction!(relaxed_state, m)?)?;
        m.add_function(wrap_pyfunction!(radial_station, m)?)?;
        Ok(())
    }
}
