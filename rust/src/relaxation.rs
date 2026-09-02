// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// SCPN RFP Core — relaxed-state kernels

//! The Bessel-function relaxed state (Paccagnella 2015, eqs. 4-5, as the
//! single-region Taylor state), operation-for-operation identical to
//! `scpn_rfp_core.physics.relaxation`.

use crate::NumericsError;
use scpn_reactor_kernels_native::numerics::bessel::{
    bessel_j0, bessel_j1, BESSEL_J0_FIRST_ZERO, BESSEL_J1_FIRST_ZERO,
};

/// `j_{0,1} / 2`: the pinch parameter at which `F_bfm = 0`.
pub const BFM_REVERSAL_PINCH_PARAMETER: f64 = BESSEL_J0_FIRST_ZERO / 2.0;
/// `j_{1,1} / 2`: the pole of `F_bfm`; the model's exclusive upper bound.
pub const BFM_MAX_PINCH_PARAMETER: f64 = BESSEL_J1_FIRST_ZERO / 2.0;

/// The relaxed state and its advisory comparisons.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct RelaxedState {
    /// `Theta`.
    pub pinch_parameter: f64,
    /// `mu = 2 Theta / a`.
    pub force_free_parameter_per_m: f64,
    /// `B0`.
    pub axis_field_t: f64,
    /// `F_bfm(Theta)`.
    pub bfm_reversal_parameter: f64,
    /// The declared `F`.
    pub declared_reversal_parameter: f64,
    /// `F - F_bfm`.
    pub reversal_mismatch: f64,
    /// `Theta > Theta_rev`.
    pub reversed: bool,
    /// `r_rev` or `None`.
    pub reversal_radius_m: Option<f64>,
    /// `B0 J1(2 Theta)`.
    pub edge_poloidal_field_bfm_t: f64,
    /// `0.2 I_p / a` (the configuration's estimate).
    pub edge_poloidal_field_current_t: f64,
    /// `(current-derived - BFM) / BFM`.
    pub edge_field_relative_mismatch: f64,
}

/// Refuse a pinch parameter outside `(0, j_{1,1} / 2)`.
///
/// # Errors
/// Returns [`NumericsError`] naming the field and the bound.
pub fn require_bfm_pinch_parameter(theta: f64) -> Result<f64, NumericsError> {
    if !theta.is_finite() {
        return Err(NumericsError {
            message: format!("pinch_parameter: must be finite, got {theta:?}"),
        });
    }
    if theta <= 0.0 {
        return Err(NumericsError {
            message: format!("pinch_parameter: must be strictly positive, got {theta:?}"),
        });
    }
    if theta >= BFM_MAX_PINCH_PARAMETER {
        return Err(NumericsError {
            message: format!(
                "pinch_parameter: the Bessel-function model is defined for Theta < j_1,1 / 2 = {BFM_MAX_PINCH_PARAMETER:?} (the average toroidal field of the relaxed state vanishes there), got {theta:?}"
            ),
        });
    }
    Ok(theta)
}

/// `mu = 2 Theta / a`.
#[must_use]
pub fn force_free_parameter(theta: f64, minor_radius_m: f64) -> f64 {
    2.0 * theta / minor_radius_m
}

/// `B0 = <B_phi> Theta / J1(2 Theta)`.
///
/// # Errors
/// Propagates the library's refusal of the Bessel argument.
pub fn axis_field(average_toroidal_field_t: f64, theta: f64) -> Result<f64, NumericsError> {
    Ok(average_toroidal_field_t * theta / bessel_j1(2.0 * theta)?)
}

/// `F_bfm = Theta J0(2 Theta) / J1(2 Theta)`.
///
/// # Errors
/// Refuses a pinch parameter outside the model's domain.
pub fn bfm_reversal_parameter(theta: f64) -> Result<f64, NumericsError> {
    require_bfm_pinch_parameter(theta)?;
    let x = 2.0 * theta;
    Ok(theta * bessel_j0(x)? / bessel_j1(x)?)
}

/// `r_rev = j_{0,1} / mu` when `Theta > Theta_rev`, else `None`.
#[must_use]
pub fn reversal_radius(theta: f64, minor_radius_m: f64) -> Option<f64> {
    if theta <= BFM_REVERSAL_PINCH_PARAMETER {
        return None;
    }
    Some(BESSEL_J0_FIRST_ZERO / force_free_parameter(theta, minor_radius_m))
}

/// Evaluate the relaxed state of one configuration.
///
/// # Errors
/// Refuses a pinch parameter outside the model's domain.
pub fn relaxed_state(
    minor_radius_m: f64,
    theta: f64,
    average_toroidal_field_t: f64,
    declared_reversal_parameter: f64,
    plasma_current_ma: f64,
) -> Result<RelaxedState, NumericsError> {
    let theta = require_bfm_pinch_parameter(theta)?;
    let mu = force_free_parameter(theta, minor_radius_m);
    let b0 = axis_field(average_toroidal_field_t, theta)?;
    let f_bfm = bfm_reversal_parameter(theta)?;
    let edge_bfm = b0 * bessel_j1(2.0 * theta)?;
    let edge_current = 0.2 * plasma_current_ma / minor_radius_m;
    Ok(RelaxedState {
        pinch_parameter: theta,
        force_free_parameter_per_m: mu,
        axis_field_t: b0,
        bfm_reversal_parameter: f_bfm,
        declared_reversal_parameter,
        reversal_mismatch: declared_reversal_parameter - f_bfm,
        reversed: theta > BFM_REVERSAL_PINCH_PARAMETER,
        reversal_radius_m: reversal_radius(theta, minor_radius_m),
        edge_poloidal_field_bfm_t: edge_bfm,
        edge_poloidal_field_current_t: edge_current,
        edge_field_relative_mismatch: (edge_current - edge_bfm) / edge_bfm,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn reversal_threshold_and_limit() {
        assert_eq!(
            bfm_reversal_parameter(BFM_REVERSAL_PINCH_PARAMETER).unwrap(),
            0.0
        );
        assert!((bfm_reversal_parameter(1.0e-3).unwrap() - 1.0).abs() < 1.0e-6);
        assert!(bfm_reversal_parameter(1.5).unwrap() < 0.0);
        assert!(bfm_reversal_parameter(BFM_MAX_PINCH_PARAMETER).is_err());
        assert!(bfm_reversal_parameter(0.0).is_err());
        assert!(reversal_radius(1.0, 0.5).is_none());
        let state = relaxed_state(0.5, 1.6, 0.25, -0.2, 1.0).unwrap();
        assert!(state.reversed);
        assert_eq!(state.force_free_parameter_per_m, 6.4);
    }
}
