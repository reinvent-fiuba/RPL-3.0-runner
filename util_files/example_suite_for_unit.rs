use student_package::*; // No borrar!

// IMPORTANTE:
// los assert reportan fallas de la forma assertion left == right failed
// Nunca se muestran los nombres de las funciones/variables que tengan.
// Es altamente recomendable que se usen mensajes descriptivos en los mismos para que el alumno pueda identificar la falla.
// Los mensajes de los assert solo se mostraran si la aserción falla.
// Este es un archivo de ejemplo.

#[test]
fn foo_no_repetido_devuelve_resultado_esperado() {
    let obtained = foo_no_repetido();
    let expected = 1;
    assert_eq!(
        obtained, expected,
        "El resultado de foo_no_repetido() no es igual a 1"
    );
}

#[test]
fn bar_no_repetido_devuelve_resultado_esperado() {
    let obtained = bar_no_repetido();
    let expected = 2;
    let msg = format!(
        "El resultado obtenido ({}) no es igual a {}",
        obtained, expected
    );
    assert_eq!(obtained, expected, "{}", msg);
    assert_ne!(
        obtained, 3,
        "El resultado de bar_no_repetido() no debe ser igual a 3"
    );
    assert!(
        obtained > 0,
        "El resultado de bar_no_repetido() debe ser mayor a 0"
    );
}
