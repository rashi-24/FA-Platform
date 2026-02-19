import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { AIChatWidgetComponent } from './features/ai-chat/ai-chat-widget.component';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, AIChatWidgetComponent],
  templateUrl: './app.html',
  styleUrl: './app.scss'
})
export class App {
  title = 'FA Platform';
}
