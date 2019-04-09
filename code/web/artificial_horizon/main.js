//
// From github page: https://github.com/richtr/Artificial-Horizon
// original author: richtr -> https://github.com/richtr
// 
// code has been modified from its original form to make it more suited to fix a problem
// The orginal author does NOT have anything to do with CISS MATE-ROV or its members
//

var artificialHorizon = (function() {

    var TWO_PI = 2 * Math.PI, HALF_PI = Math.PI / 2, KAPPA = 0.5522847498, radius_mul_kappa;
    
    var GROUND_COLOR = "#72cde4", LINE_COLOR = "#ffffff", SKY_COLOR = "#323232";

    var canvas, context;

    var diameter = 0, radius = 0;

    var pitch = 0, roll = 0;//-Math.PI/12;

    var horizon, aspectRatio = 0;
    
    var rotationCorrection = 0;

    function draw() {

        aspectRatio = document.body.clientWidth / document.body.clientHeight;

        if (rotationCorrection !== 0 && (rotationCorrection % HALF_PI) == 0
                && (rotationCorrection / HALF_PI) !== 1) {

            aspectRatio = document.body.clientHeight / document.body.clientWidth;

        }

        diameter = Math.min(canvas.width, canvas.height);
        radius = diameter / 2;

        radius_mul_kappa = radius * KAPPA;
        
        // calculate horizon
        horizon = getHorizon(pitch);
        
        // repaint
        repaint();
        
        requestAnimationFrame(draw);

    }

    function repaint() {

        context.save();
        
        context.translate(radius, radius);
        context.rotate(roll - rotationCorrection);
        
        context.fillStyle = GROUND_COLOR;
        context.strokeStyle = LINE_COLOR;
        context.lineWidth = 3;

        // draw ground
        context.beginPath();
        context.arc(0, 0, radius, 0, 2 * Math.PI, false);
        context.fill();
        
        context.fillStyle = SKY_COLOR;

        // draw sky
        context.beginPath();
        context.moveTo( -radius, 0);
        context.arcTo(0, -radius*2, radius, 0, radius);
        context.bezierCurveTo(radius, horizon * KAPPA, radius_mul_kappa, horizon, 0, horizon);
        context.bezierCurveTo( -radius_mul_kappa, horizon, -radius, horizon * KAPPA, -radius, 0);
        context.closePath();
        context.stroke();
        context.fill();

        context.lineWidth = 2;
        
        // draw scale
        drawScale(36, radius * 0.8);
        drawScale(30, radius * 0.1);
        drawScale(24, radius * 0.6);
        drawScale(18, radius * 0.1);
        drawScale(12, radius * 0.4);
        drawScale(6, radius * 0.1);

        context.restore();

    }

    function drawScale(offset, scaleWidth) {

        context.save();

        context.beginPath();
        context.rect( -scaleWidth / 2, -diameter, scaleWidth, 2 * diameter);
        context.clip();

        horizon = getHorizon(pitch + offset * Math.PI / 180);
        context.beginPath();
        context.moveTo(radius, 0);
        context.bezierCurveTo(radius, horizon * KAPPA, radius_mul_kappa, horizon, 0, horizon);
        context.bezierCurveTo( -radius_mul_kappa, horizon, -radius, horizon * KAPPA, -radius, 0);
        context.stroke();

        horizon = getHorizon(pitch -offset * Math.PI / 180);
        context.beginPath();
        context.moveTo(radius, 0);
        context.bezierCurveTo(radius, horizon * KAPPA, radius_mul_kappa, horizon, 0, horizon);
        context.bezierCurveTo( -radius_mul_kappa, horizon, -radius, horizon * KAPPA, -radius, 0);
        context.stroke();
        
        context.restore();

    }

    function getHorizon(pitch) {

        return Math.sin(pitch) * radius;

    }
    
    function drawRotationCorrectionButton() {

        var rotationCorrectButton = document.createElement('div');
        rotationCorrectButton.style.position = "fixed";
        rotationCorrectButton.style.display = "block";
        rotationCorrectButton.style.top = "10px";
        rotationCorrectButton.style.right = "10px";
        rotationCorrectButton.style.width = "32px";
        rotationCorrectButton.style.height = "32px";
        rotationCorrectButton.style.padding = "10px";
        rotationCorrectButton.textContent = "Rotate";
        rotationCorrectButton.style.backgroundImage = "url('images/rotate.png')";
        rotationCorrectButton.style.backgroundPosition = "center";
        rotationCorrectButton.style.backgroundRepeat = "no-repeat";
        rotationCorrectButton.style.border = "3px solid #030303";
        rotationCorrectButton.style.textIndent = "-9999px";

        rotationCorrectButton.addEventListener('click',
        function(e) {
            rotationCorrection -= HALF_PI;
        },
        true);

        document.body.appendChild(rotationCorrectButton);

    }

    function run() {        

        draw();

    }

    return {
        initAndRun: function() {

            canvas = document.getElementById("canvas");
            context = canvas.getContext("2d");

            var topImage = new Image();
            topImage.onload = function() {
                run();
            }
            topImage.src = "images/tool_320_2.png";
        }

    };

})();

window.addEventListener("load", function() {
    artificialHorizon.initAndRun();
}, false);


