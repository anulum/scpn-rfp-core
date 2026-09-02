// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// SCPN RFP Core — radial profile kernels

//! Field and safety-factor profile of the Bessel-function relaxed state,
//! operation-for-operation identical to `scpn_rfp_core.physics.profiles`.

use crate::NumericsError;
use scpn_reactor_kernels_native::numerics::bessel::{bessel_j0, bessel_j1};

/// The relaxed-state fields at one normalised radius.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct RadialStation {
    /// `r / a`.
    pub fraction: f64,
    /// `r`.
    pub radius_m: f64,
    /// `B_phi(r) = B0 J0(mu r)`.
    pub toroidal_field_t: f64,
    /// `B_theta(r) = B0 J1(mu r)`.
    pub poloidal_field_t: f64,
    /// `q(r)`; the series limit on the axis.
    pub safety_factor: f64,
}

/// Refuse a station outside `[0, 1]`.
///
/// # Errors
/// Returns [`NumericsError`] naming the field and the bound.
pub fn require_station(name: &str, fraction: f64) -> Result<f64, NumericsError> {
    if !fraction.is_finite() {
        return Err(NumericsError {
            message: format!("{name}: must be finite, got {fraction:?}"),
        });
    }
    if !(0.0..=1.0).contains(&fraction) {
        return Err(NumericsError {
            message: format!("{name}: a radial station is r / a within [0, 1], got {fraction:?}"),
        });
    }
    Ok(fraction)
}

/// `q(0) = a / (Theta R0)`.
#[must_use]
pub fn axis_safety_factor(minor_radius_m: f64, major_radius_m: f64, theta: f64) -> f64 {
    minor_radius_m / (theta * major_radius_m)
}

/// Evaluate the fields and `q` at one station.
///
/// # Errors
/// Refuses a station outside `[0, 1]` and propagates the library's refusal.
pub fn radial_station(
    fraction: f64,
    minor_radius_m: f64,
    major_radius_m: f64,
    theta: f64,
    axis_field_t: f64,
) -> Result<RadialStation, NumericsError> {
    require_station("fraction", fraction)?;
    let radius = fraction * minor_radius_m;
    let x = 2.0 * theta * fraction;
    let j0 = bessel_j0(x)?;
    let j1 = bessel_j1(x)?;
    let q = if fraction == 0.0 {
        axis_safety_factor(minor_radius_m, major_radius_m, theta)
    } else {
        (radius / major_radius_m) * j0 / j1
    };
    Ok(RadialStation {
        fraction,
        radius_m: radius,
        toroidal_field_t: axis_field_t * j0,
        poloidal_field_t: axis_field_t * j1,
        safety_factor: q,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn axis_station_and_refusal() {
        let station = radial_station(0.0, 0.5, 2.0, 1.6, 1.5).unwrap();
        assert_eq!(station.poloidal_field_t, 0.0);
        assert_eq!(station.toroidal_field_t, 1.5);
        assert_eq!(station.safety_factor, 0.5 / (1.6 * 2.0));
        assert!(radial_station(1.5, 0.5, 2.0, 1.6, 1.5).is_err());
        assert!(radial_station(f64::NAN, 0.5, 2.0, 1.6, 1.5).is_err());
    }
}
