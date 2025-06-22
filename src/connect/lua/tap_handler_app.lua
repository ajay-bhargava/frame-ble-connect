
local data = require('data.min')
local camera = require('camera.min')
local plain_text = require('plain_text.min')

-- Message type constants for communication protocol
CAPTURE_SETTINGS_MSG = 0x0d
TEXT_DISPLAY_MSG = 0x11
TAP_DETECTED_MSG = 0x12

-- Register message parsers for automatic processing
data.parsers[CAPTURE_SETTINGS_MSG] = camera.parse_capture_settings
data.parsers[TEXT_DISPLAY_MSG] = plain_text.parse_plain_text

-- Visual feedback functions for better UX
function clear_display()
    frame.display.text(" ", 1, 1)
    frame.display.show()
    frame.sleep(0.04)
end

function show_capture_flash()
    -- Brief white flash to indicate photo capture
    frame.display.bitmap(241, 191, 160, 2, 0, string.rep("\xFF", 400))
    frame.display.bitmap(311, 121, 20, 2, 0, string.rep("\xFF", 400))
    frame.display.show()
    frame.sleep(0.04)
end

function show_tap_indicator()
    -- Quick visual confirmation of tap detection
    frame.display.text("TAP!", 200, 100)
    frame.display.show()
    frame.sleep(0.2)
    clear_display()
end

-- Tap callback function - called when user taps the glasses
function on_tap()
    print("TAP_DETECTED")  -- Send tap event to host
    show_tap_indicator()
    
    -- Auto-trigger photo capture on tap
    -- This provides immediate feedback to user action
    local capture_settings = {
        resolution = 720,
        auto_exposure = true,
        quality = 80
    }
    
    show_capture_flash()
    rc, err = pcall(camera.capture_and_send, capture_settings)
    clear_display()
    
    if rc == false then
        print("CAPTURE_ERROR: " .. tostring(err))
    else
        print("CAPTURE_SUCCESS")
    end
end

-- Register the tap callback with Frame system
frame.register_tap_callback(on_tap)

-- Main application event loop
function app_loop()
    clear_display()
    frame.display.text("Ready for taps", 1, 1)
    frame.display.show()
    
    -- Signal to host that Frame app is ready
    print('Frame app is running')
    
    while true do
        rc, err = pcall(
            function()
                -- Process incoming messages from host
                local items_ready = data.process_raw_items()
                
                if items_ready > 0 then
                    -- Handle manual capture requests from host
                    if data.app_data[CAPTURE_SETTINGS_MSG] ~= nil then
                        show_capture_flash()
                        rc, err = pcall(camera.capture_and_send, data.app_data[CAPTURE_SETTINGS_MSG])
                        clear_display()
                        
                        if rc == false then
                            print("MANUAL_CAPTURE_ERROR: " .. tostring(err))
                        else 
                            print("MANUAL_CAPTURE_SUCCESS")
                        end
                        
                        data.app_data[CAPTURE_SETTINGS_MSG] = nil
                    end
                    
                    -- Handle text display requests
                    if data.app_data[TEXT_DISPLAY_MSG] ~= nil then
                        local text_data = data.app_data[TEXT_DISPLAY_MSG]
                        clear_display()
                        frame.display.text(text_data.text, 1, 1)
                        frame.display.show()
                        data.app_data[TEXT_DISPLAY_MSG] = nil
                    end
                end
                
                -- Run camera auto-exposure when enabled
                if camera.is_auto_exp then
                    camera.run_auto_exposure()
                end
                
                -- Short sleep to prevent excessive CPU usage
                frame.sleep(0.05)
            end
        )
        
        -- Handle errors and break signals gracefully
        if rc == false then
            print("APP_ERROR: " .. tostring(err))
            clear_display()
            break
        end
    end
end

-- Start the main application loop
app_loop()
