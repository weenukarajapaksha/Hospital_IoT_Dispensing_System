# Run The Two Simulators

This project has two VS Code workspace folders for Wokwi:

- `SupplyWindow` runs the supply controller simulation.
- `TankWindow` runs the dispensing tank controller simulation.

Open them in two separate VS Code windows.

## Window 1: Supply

Open:

```text
C:\Users\ASUS VIVOBOOK\Documents\PlatformIO\Projects\Hospital230515N\SupplyWindow
```

Build:

```powershell
& "$env:USERPROFILE\.platformio\penv\Scripts\pio.exe" run
```

Then run `Wokwi: Start Simulator`.

## Window 2: Tank

Open:

```text
C:\Users\ASUS VIVOBOOK\Documents\PlatformIO\Projects\Hospital230515N\TankWindow
```

Build:

```powershell
& "$env:USERPROFILE\.platformio\penv\Scripts\pio.exe" run
```

Then run `Wokwi: Start Simulator`.

## Note

These two Wokwi windows are useful for checking each side's LCD, sensors, and outputs independently. For full ESP-NOW communication between the two controllers, use two real ESP32 boards.
