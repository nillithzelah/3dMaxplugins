# encoding: UTF-8
require 'sketchup.rb'

module SketchUpPluginCollection
  module SketchUpPanel
    PLUGIN_NAME = 'Sketch Up'
    DIALOG_TITLE = 'Sketch Up 面板'
    HTML_FILE = File.join(__dir__, 'index.html')

    unless file_loaded?(__FILE__)
      UI.menu('Plugins').add_item(PLUGIN_NAME) {
        show_dialog
      }
      toolbar = UI::Toolbar.new(PLUGIN_NAME)
      cmd = UI::Command.new('打开Sketch Up面板') {
        show_dialog
      }
      icon_path = File.join(__dir__, 'icon.png')
      if File.exist?(icon_path)
        cmd.small_icon = icon_path
        cmd.large_icon = icon_path
      end
      cmd.tooltip = '打开Sketch Up面板'
      cmd.status_bar_text = '打开Sketch Up面板'
      toolbar.add_item(cmd)
      toolbar.show
      file_loaded(__FILE__)
    end

    def self.show_dialog
      dlg = UI::HtmlDialog.new(
        {
          :dialog_title => DIALOG_TITLE,
          :preferences_key => PLUGIN_NAME,
          :scrollable => true,
          :resizable => true,
          :width => 600,
          :height => 800,
          :left => 100,
          :top => 100,
          :style => UI::HtmlDialog::STYLE_DIALOG
        }
      )
      dlg.set_file(HTML_FILE)

      # 注册回调
      dlg.add_action_callback("get_current_view") do |action_context|
        require 'base64'
        model = Sketchup.active_model
        view = model.active_view
        img_path = File.join(Dir.tmpdir, "current_view.png")
        view.write_image(img_path, 800, 600, false, 0.0)
        if File.exist?(img_path)
          base64 = Base64.strict_encode64(File.binread(img_path))
          dlg.execute_script("showCurrentView('" + base64 + "')")
          File.delete(img_path) rescue nil
        else
          dlg.execute_script("showCurrentView('')")
        end
      end

      dlg.show
    end
  end
end 